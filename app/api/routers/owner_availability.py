from datetime import date, datetime, time
from uuid import UUID

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.db import get_db
from app.schemas.owner_availability import (
    AvailabilityRuleCreate,
    AvailabilityRuleOut,
    AvailabilityRuleUpdate,
    BlockedSlotCreate,
    BlockedSlotOut,
    OwnerAvailabilitySlotOut,
)
from app.services.owner_availability_service import OwnerAvailabilityService
from app.api.dependencies.auth import get_current_owner_user # You'll need to implement owner authentication
from typing import Any # Add this line

router = APIRouter(prefix="/owner/{workspace_id}/availability", tags=["owner-availability"])


@router.post(
    "/rules",
    response_model=AvailabilityRuleOut,
    status_code=status.HTTP_201_CREATED,
)
def create_availability_rule(
    workspace_id: UUID,
    rule: AvailabilityRuleCreate,
    db: Session = Depends(get_db),
    current_owner: Any = Depends(get_current_owner_user), # Protect this endpoint
):
    """
    Creates a new recurring availability rule for the owner.
    """
    service = OwnerAvailabilityService(db)
    return service.create_availability_rule(workspace_id, rule)


@router.get(
    "/rules",
    response_model=list[AvailabilityRuleOut],
)
def list_availability_rules(
    workspace_id: UUID,
    db: Session = Depends(get_db),
    current_owner: Any = Depends(get_current_owner_user), # Protect this endpoint
):
    """
    Lists all recurring availability rules for the owner.
    """
    service = OwnerAvailabilityService(db)
    return service.list_availability_rules(workspace_id)


@router.put(
    "/rules/{rule_id}",
    response_model=AvailabilityRuleOut,
)
def update_availability_rule(
    workspace_id: UUID,
    rule_id: UUID,
    rule_update: AvailabilityRuleUpdate,
    db: Session = Depends(get_db),
    current_owner: Any = Depends(get_current_owner_user), # Protect this endpoint
):
    """
    Updates an existing recurring availability rule.
    """
    service = OwnerAvailabilityService(db)
    updated_rule = service.update_availability_rule(workspace_id, rule_id, rule_update)
    if not updated_rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Availability rule not found")
    return updated_rule


@router.delete(
    "/rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_availability_rule(
    workspace_id: UUID,
    rule_id: UUID,
    db: Session = Depends(get_db),
    current_owner: Any = Depends(get_current_owner_user), # Protect this endpoint
):
    """
    Deletes a recurring availability rule.
    """
    service = OwnerAvailabilityService(db)
    if not service.delete_availability_rule(workspace_id, rule_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Availability rule not found")
    return


@router.post(
    "/blocked-slots",
    response_model=BlockedSlotOut,
    status_code=status.HTTP_201_CREATED,
)
def create_blocked_slot(
    workspace_id: UUID,
    blocked_slot: BlockedSlotCreate,
    db: Session = Depends(get_db),
    current_owner: Any = Depends(get_current_owner_user), # Protect this endpoint
):
    """
    Creates a specific blocked time slot for the owner.
    """
    service = OwnerAvailabilityService(db)
    return service.create_blocked_slot(workspace_id, blocked_slot)


@router.get(
    "/blocked-slots",
    response_model=list[BlockedSlotOut],
)
def list_blocked_slots(
    workspace_id: UUID,
    from_date: date,
    to_date: date,
    db: Session = Depends(get_db),
    current_owner: Any = Depends(get_current_owner_user), # Protect this endpoint
):
    """
    Lists all specific blocked time slots for the owner within a date range.
    """
    service = OwnerAvailabilityService(db)
    return service.list_blocked_slots(workspace_id, from_date, to_date)


@router.delete(
    "/blocked-slots/{slot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_blocked_slot(
    workspace_id: UUID,
    slot_id: UUID,
    db: Session = Depends(get_db),
    current_owner: Any = Depends(get_current_owner_user), # Protect this endpoint
):
    """
    Deletes a specific blocked time slot.
    """
    service = OwnerAvailabilityService(db)
    if not service.delete_blocked_slot(workspace_id, slot_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blocked slot not found")
    return


@router.get(
    "/calendar",
    response_model=list[OwnerAvailabilitySlotOut],
)
# Removed the duplicate @router.get("/owner/availability") as it was inconsistent with the path prefix
async def get_owner_availability(
    workspace_id: UUID, # Add workspace_id as a path parameter
    from_date: date,     # Add from_date as a query parameter
    to_date: date,       # Add to_date as a query parameter
    db: Session = Depends(get_db), # Add db dependency
    current_owner: Any = Depends(get_current_owner_user), # Protect this endpoint
):
    """
    Returns a consolidated view of the owner's availability for a given date range,
    combining recurring rules and specific blocked slots. This is for the owner's UI.
    """
    service = OwnerAvailabilityService(db)
    return service.get_owner_availability_calendar(workspace_id, from_date, to_date)