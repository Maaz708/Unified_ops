from __future__ import annotations

# app/models/inventory_usage_log.py
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base
from .mixins import UUIDMixin, TimestampMixin, WorkspaceScopedMixin

if TYPE_CHECKING:
    from .workspace import Workspace
    from .inventory_item import InventoryItem
    from .booking import Booking


class InventoryUsageLog(Base, UUIDMixin, TimestampMixin, WorkspaceScopedMixin):
    __tablename__ = "inventory_usage_logs"
    __table_args__ = (
        Index(
            "ix_inventory_usage_workspace_item",
            "workspace_id",
            "item_id",
            "created_at",
        ),
    )

    item_id: Mapped["uuid.UUID"] = mapped_column(
        ForeignKey("inventory_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    booking_id: Mapped["uuid.UUID | None"] = mapped_column(
        ForeignKey("bookings.id", ondelete="SET NULL"),
        nullable=True,
    )
    quantity_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255))

    workspace: Mapped["Workspace"] = relationship(
        "Workspace", back_populates="inventory_usage_logs"
    )
    item: Mapped["InventoryItem"] = relationship(
        "InventoryItem", back_populates="usage_logs"
    )
    booking: Mapped["Booking | None"] = relationship(
        "Booking", back_populates="inventory_usage_logs"
    )