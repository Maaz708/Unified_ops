# app/services/inventory_service.py
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.booking import Booking, BookingStatus
from app.models.inventory_item import InventoryItem
from app.models.inventory_usage_log import InventoryUsageLog
from app.models.alert import Alert, AlertSeverity, AlertSource
from app.models.event_log import EventLog, ActorType


class InventoryService:
    """
    Inventory domain logic:

    - Deduct inventory when a booking is completed
    - Record usage logs per booking
    - Raise low-stock alerts
    - Log all important events
    """

    def __init__(self, db: Session):
        self.db = db

    # ---------- Public API ----------

    def deduct_for_booking(
        self,
        workspace_id: UUID,
        booking_id: UUID,
        usage_spec: list[tuple[UUID, int]],
    ) -> None:
        """
        usage_spec: list of (inventory_item_id, quantity_to_deduct)
        Called when booking is marked completed.
        """
        booking = self._get_booking(workspace_id, booking_id)

        if booking.status != BookingStatus.completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking must be completed before deducting inventory.",
            )

        # Load all items for workspace and referenced ids
        item_ids = [item_id for (item_id, _) in usage_spec]
        items = self.db.scalars(
            select(InventoryItem).where(
                InventoryItem.workspace_id == workspace_id,
                InventoryItem.id.in_(item_ids),
                InventoryItem.is_deleted.is_(False),
            )
        ).all()
        items_by_id = {i.id: i for i in items}

        if len(items_by_id) != len(set(item_ids)):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more inventory items not found in workspace.",
            )

        for item_id, qty in usage_spec:
            if qty <= 0:
                continue
            item = items_by_id[item_id]

            # Deduct
            item.current_quantity -= qty

            log = InventoryUsageLog(
                workspace_id=workspace_id,
                item_id=item.id,
                booking_id=booking.id,
                quantity_delta=-qty,
                reason=f"Booking {booking.id} completed",
            )
            self.db.add(log)

            # Log event per item
            self._log_event(
                workspace_id=workspace_id,
                event_type="inventory.item_deducted",
                entity_type="inventory_item",
                entity_id=str(item.id),
                payload={
                    "booking_id": str(booking.id),
                    "quantity_delta": -qty,
                    "new_quantity": item.current_quantity,
                },
            )

            # Threshold check
            self._check_threshold_and_alert(item)

        # Log booking-level inventory event
        self._log_event(
            workspace_id=workspace_id,
            event_type="inventory.deducted_for_booking",
            entity_type="booking",
            entity_id=str(booking.id),
            payload={
                "items": [
                    {"item_id": str(i), "quantity": q} for i, q in usage_spec
                ]
            },
        )

        self.db.commit()

    # ---------- Internal helpers ----------

    def _get_booking(self, workspace_id: UUID, booking_id: UUID) -> Booking:
        booking = self.db.scalar(
            select(Booking).where(
                Booking.workspace_id == workspace_id,
                Booking.id == booking_id,
                Booking.is_deleted.is_(False),
            )
        )
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found for workspace.",
            )
        return booking

    def _check_threshold_and_alert(self, item: InventoryItem) -> None:
        if item.reorder_threshold is None:
            return
        if item.current_quantity >= item.reorder_threshold:
            return

        # Create alert
        alert = Alert(
            workspace_id=item.workspace_id,
            severity=AlertSeverity.warning,
            source=AlertSource.system,
            code="inventory.low_stock",
            message=(
                f"Inventory item '{item.name}' ({item.sku}) is below threshold: "
                f"{item.current_quantity} {item.unit or ''} remaining "
                f"(threshold {item.reorder_threshold})."
            ),
            context={
                "inventory_item_id": str(item.id),
                "sku": item.sku,
                "current_quantity": item.current_quantity,
                "reorder_threshold": item.reorder_threshold,
            },
        )
        self.db.add(alert)

        # Log event
        self._log_event(
            workspace_id=item.workspace_id,
            event_type="inventory.low_stock",
            entity_type="inventory_item",
            entity_id=str(item.id),
            payload={
                "sku": item.sku,
                "current_quantity": item.current_quantity,
                "reorder_threshold": item.reorder_threshold,
                "alert_id": str(alert.id),
            },
        )

    def _log_event(
        self,
        workspace_id: UUID,
        event_type: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        payload: Optional[dict] = None,
    ) -> None:
        ev = EventLog(
            workspace_id=workspace_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_type=ActorType.system,
            payload=payload or {},
        )
        self.db.add(ev)