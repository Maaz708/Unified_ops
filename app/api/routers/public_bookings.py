# app/api/routers/public_bookings.py
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.api.dependencies.db import get_db
from app.schemas.booking import (
    PublicBookingTypeOut,
    PublicAvailabilitySlotOut,
    PublicBookingCreateRequest,
    PublicBookingResponse,
)
from app.services.public_booking_service import PublicBookingService

router = APIRouter(prefix="/public", tags=["public-bookings"])


@router.get(
    "/{workspace_id}/booking-types",
    response_model=list[PublicBookingTypeOut],
)
def list_public_booking_types(
    workspace_id: UUID,
    db: Session = Depends(get_db),
):
    service = PublicBookingService(db)
    return service.list_booking_types(workspace_id)


@router.get(
    "/{workspace_id}/booking-types/{slug}/availability",
    response_model=list[PublicAvailabilitySlotOut],
)
def get_public_availability_for_date(
    workspace_id: UUID,
    slug: str,
    day: date,
    db: Session = Depends(get_db),
):
    """
    Returns availability slots for the given day (UTC) and booking type.
    """
    service = PublicBookingService(db)
    return service.get_availability_for_date(workspace_id, slug, day)


@router.get(
    "/{workspace_id}/booking-types/{slug}/availability-range",
    response_model=list[date],
)
def get_public_availability_range(
    workspace_id: UUID,
    slug: str,
    from_date: date,
    to_date: date,
    db: Session = Depends(get_db),
):
    """
    Returns dates in [from_date, to_date] that have at least one available slot.
    Use this to show a month calendar: only these dates are bookable.
    """
    if to_date < from_date:
        return []
    service = PublicBookingService(db)
    return service.get_available_dates_in_range(workspace_id, slug, from_date, to_date)


@router.post(
    "/{workspace_id}/bookings",
    response_model=PublicBookingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_public_booking(
    workspace_id: UUID,
    payload: PublicBookingCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Public booking endpoint (no authentication):
    - creates/uses contact
    - creates/uses conversation
    - creates booking (double-booking safe)
    - queues confirmation email via BackgroundTasks
    - logs events for analytics/automation
    """
    service = PublicBookingService(db)
    return service.create_public_booking(workspace_id, payload, background_tasks)