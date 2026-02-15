# app/api/routers/workspaces.py
from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.db import get_db
from app.models.workspace import Workspace, WorkspaceStatus
from app.models.workspace_email_config import WorkspaceEmailConfig
from app.models.availability_slot import AvailabilitySlot
from app.models.booking_type import BookingType
from app.models.users import StaffUser
from app.schemas.workspace import (
    WorkspaceOnboardingRequest,
    WorkspaceOnboardingResponse,
    WorkspaceEmailConfigOut,
    WorkspaceEmailConfigUpdate,
    OnboardingValidationStatus,
    AvailabilitySlotOut,
    AvailabilitySlotCreateRequest,
)
from app.services.workspace_service import WorkspaceOnboardingService
from app.core.security import hash_password
from datetime import timezone

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


def _get_workspace_or_403(db: Session, workspace_id: UUID, current_user: dict) -> Workspace:
    if str(current_user["workspace_id"]) != str(workspace_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your workspace")
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return ws


@router.post(
    "/onboard",
    response_model=WorkspaceOnboardingResponse,
    status_code=status.HTTP_201_CREATED,
)
def onboard_workspace(
    payload: WorkspaceOnboardingRequest,
    db: Session = Depends(get_db),
):
    """
    Complete workspace onboarding in a single transactional flow:
    - create workspace
    - create owner
    - connect email provider
    - create booking types
    - define availability
    - validate and activate/pending
    """
    service = WorkspaceOnboardingService(db)
    return service.onboard_workspace(payload)


@router.get(
    "/{workspace_id}/email-config",
    response_model=WorkspaceEmailConfigOut,
)
def get_workspace_email_config(
    workspace_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if str(current_user["workspace_id"]) != str(workspace_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your workspace")
    cfg = db.query(WorkspaceEmailConfig).filter(
        WorkspaceEmailConfig.workspace_id == workspace_id,
    ).first()
    if not cfg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email config not found")
    return WorkspaceEmailConfigOut.model_validate(cfg)


@router.patch(
    "/{workspace_id}/email-config",
    response_model=WorkspaceEmailConfigOut,
)
def update_workspace_email_config(
    workspace_id: UUID,
    payload: WorkspaceEmailConfigUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if str(current_user["workspace_id"]) != str(workspace_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your workspace")
    cfg = db.query(WorkspaceEmailConfig).filter(
        WorkspaceEmailConfig.workspace_id == workspace_id,
    ).first()
    if not cfg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email config not found")
    if payload.from_email is not None:
        cfg.from_email = payload.from_email
    if payload.from_name is not None:
        cfg.from_name = payload.from_name
    if payload.api_key_alias is not None:
        cfg.api_key_alias = payload.api_key_alias
    db.commit()
    db.refresh(cfg)
    return WorkspaceEmailConfigOut.model_validate(cfg)


class WorkspaceStatusResponse(BaseModel):
    status: str
    validation: OnboardingValidationStatus


@router.get(
    "/{workspace_id}/status",
    response_model=WorkspaceStatusResponse,
)
def get_workspace_status(
    workspace_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Return current workspace status and activation validation (for Setup/Activate UI)."""
    ws = _get_workspace_or_403(db, workspace_id, current_user)
    service = WorkspaceOnboardingService(db)
    validation = service._evaluate_activation_requirements(ws)
    return WorkspaceStatusResponse(
        status=ws.status.value,
        validation=validation,
    )


@router.post(
    "/{workspace_id}/activate",
    response_model=WorkspaceStatusResponse,
)
def activate_workspace(
    workspace_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Activate workspace if validation passes (owner only). Required for public booking page."""
    if current_user.get("role") != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owners can activate the workspace")
    ws = _get_workspace_or_403(db, workspace_id, current_user)
    service = WorkspaceOnboardingService(db)
    validation = service._evaluate_activation_requirements(ws)
    if not validation.can_activate:
        reasons_str = "; ".join(validation.reasons) if validation.reasons else "Requirements not met"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot activate until requirements are met: {reasons_str}",
        )
    ws.status = WorkspaceStatus.active
    db.commit()
    db.refresh(ws)
    return WorkspaceStatusResponse(status=ws.status.value, validation=validation)


@router.get(
    "/{workspace_id}/availability-slots",
    response_model=List[AvailabilitySlotOut],
)
def list_availability_slots(
    workspace_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all availability slots for the workspace (owner/staff)."""
    ws = _get_workspace_or_403(db, workspace_id, current_user)
    slots = db.query(AvailabilitySlot).join(BookingType).filter(
        AvailabilitySlot.workspace_id == workspace_id,
        BookingType.is_deleted.is_(False),
    ).order_by(AvailabilitySlot.start_at).all()
    result = []
    for s in slots:
        bt = db.query(BookingType).filter(BookingType.id == s.booking_type_id).first()
        staff_name = None
        if s.staff_user_id:
            staff = db.query(StaffUser).filter(StaffUser.id == s.staff_user_id).first()
            staff_name = staff.full_name if staff else None
        result.append(AvailabilitySlotOut(
            id=str(s.id),
            booking_type_slug=bt.slug if bt else "",
            booking_type_name=bt.name if bt else "",
            start_at=s.start_at,
            end_at=s.end_at,
            staff_name=staff_name,
        ))
    return result


@router.post(
    "/{workspace_id}/availability-slots",
    response_model=AvailabilitySlotOut,
    status_code=status.HTTP_201_CREATED,
)
def create_availability_slot(
    workspace_id: UUID,
    payload: AvailabilitySlotCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Add an availability slot (owner/staff)."""
    ws = _get_workspace_or_403(db, workspace_id, current_user)
    bt = db.query(BookingType).filter(
        BookingType.workspace_id == workspace_id,
        BookingType.slug == payload.booking_type_slug,
        BookingType.is_deleted.is_(False),
    ).first()
    if not bt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking type not found")
    staff_user_id = None
    if payload.staff_email:
        staff = db.query(StaffUser).filter(
            StaffUser.workspace_id == workspace_id,
            StaffUser.email == payload.staff_email,
            StaffUser.is_deleted.is_(False),
        ).first()
        if not staff:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff user not found")
        staff_user_id = staff.id
    start_at = payload.start_at
    end_at = payload.end_at
    # Keep database local time - don't convert to UTC
    if end_at <= start_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_at must be after start_at")
    slot = AvailabilitySlot(
        workspace_id=workspace_id,
        booking_type_id=bt.id,
        staff_user_id=staff_user_id,
        start_at=start_at,
        end_at=end_at,
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    staff_name = None
    if slot.staff_user_id:
        staff = db.query(StaffUser).filter(StaffUser.id == slot.staff_user_id).first()
        staff_name = staff.full_name if staff else None
    return AvailabilitySlotOut(
        id=str(slot.id),
        booking_type_slug=bt.slug,
        booking_type_name=bt.name,
        start_at=slot.start_at,
        end_at=slot.end_at,
        staff_name=staff_name,
    )


@router.delete(
    "/{workspace_id}/availability-slots/{slot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_availability_slot(
    workspace_id: UUID,
    slot_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete an availability slot (owner/staff)."""
    ws = _get_workspace_or_403(db, workspace_id, current_user)
    slot = db.query(AvailabilitySlot).filter(
        AvailabilitySlot.id == slot_id,
        AvailabilitySlot.workspace_id == workspace_id,
    ).first()
    if not slot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")
    db.delete(slot)
    db.commit()
    return None