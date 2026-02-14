# app/api/routers/forms.py
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.db import get_db
from app.models.workspace import Workspace
from app.models.form_template import FormTemplate
from app.models.form_submission import FormSubmission
from app.models.booking_type import BookingType
from app.models.booking import Booking, BookingStatus
from app.models.contact import Contact
from app.schemas.form import (
    FormTemplateCreate,
    FormTemplateUpdate,
    FormTemplateOut,
    FormSubmissionOut,
)
from pydantic import BaseModel

router = APIRouter()


def _get_workspace_or_403(db: Session, workspace_id: UUID, current_user: dict) -> Workspace:
    if str(current_user["workspace_id"]) != str(workspace_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your workspace")
    ws = db.get(Workspace, workspace_id)
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return ws


@router.get(
    "/{workspace_id}/forms",
    response_model=list[FormTemplateOut],
)
def list_form_templates(
    workspace_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    _get_workspace_or_403(db, workspace_id, current_user)
    templates = db.scalars(
        select(FormTemplate).where(
            FormTemplate.workspace_id == workspace_id,
            FormTemplate.is_deleted.is_(False),
        ).order_by(FormTemplate.name)
    ).all()
    return [FormTemplateOut.model_validate(t) for t in templates]


@router.post(
    "/{workspace_id}/forms",
    response_model=FormTemplateOut,
    status_code=status.HTTP_201_CREATED,
)
def create_form_template(
    workspace_id: UUID,
    payload: FormTemplateCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ws = _get_workspace_or_403(db, workspace_id, current_user)
    if payload.booking_type_id:
        bt = db.get(BookingType, payload.booking_type_id)
        if not bt or bt.workspace_id != workspace_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid booking_type_id")
    template = FormTemplate(
        workspace_id=ws.id,
        name=payload.name,
        description=payload.description,
        schema=payload.schema_,
        active=payload.active,
        booking_type_id=payload.booking_type_id,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return FormTemplateOut.model_validate(template)


@router.get(
    "/{workspace_id}/forms/submissions",
    response_model=list[FormSubmissionOut],
)
def list_form_submissions(
    workspace_id: UUID,
    template_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    _get_workspace_or_403(db, workspace_id, current_user)
    q = select(FormSubmission).where(
        FormSubmission.workspace_id == workspace_id,
    ).order_by(FormSubmission.submitted_at.desc())
    if template_id:
        q = q.where(FormSubmission.form_template_id == template_id)
    submissions = db.scalars(q).all()
    return [FormSubmissionOut.model_validate(s) for s in submissions]


class PendingFormBookingOut(BaseModel):
    booking_id: UUID
    contact_id: UUID
    contact_name: str | None
    contact_email: str | None
    contact_phone: str | None
    form_template_id: UUID
    form_name: str
    booking_start_at: datetime

    class Config:
        from_attributes = True


@router.get(
    "/{workspace_id}/forms/pending-bookings",
    response_model=list[PendingFormBookingOut],
)
def list_pending_form_bookings(
    workspace_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Completed bookings that have a form linked to their booking type but no form submission yet."""
    _get_workspace_or_403(db, workspace_id, current_user)
    subq = (
        select(FormSubmission.booking_id).where(
            FormSubmission.workspace_id == workspace_id
        )
    )
    stmt = (
        select(Booking, Contact, FormTemplate)
        .join(Contact, Booking.contact_id == Contact.id)
        .join(FormTemplate, and_(
            FormTemplate.workspace_id == workspace_id,
            FormTemplate.booking_type_id == Booking.booking_type_id,
            FormTemplate.is_deleted.is_(False),
            FormTemplate.active.is_(True),
        ))
        .where(
            Booking.workspace_id == workspace_id,
            Booking.status == BookingStatus.completed,
            Booking.id.not_in(subq),
        )
        .order_by(Booking.start_at.desc())
    )
    rows = db.execute(stmt).all()
    return [
        PendingFormBookingOut(
            booking_id=b.id,
            contact_id=c.id,
            contact_name=c.full_name,
            contact_email=c.primary_email,
            contact_phone=c.primary_phone,
            form_template_id=ft.id,
            form_name=ft.name,
            booking_start_at=b.start_at,
        )
        for b, c, ft in rows
    ]


@router.get(
    "/{workspace_id}/forms/{template_id}",
    response_model=FormTemplateOut,
)
def get_form_template(
    workspace_id: UUID,
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    _get_workspace_or_403(db, workspace_id, current_user)
    template = db.scalar(
        select(FormTemplate).where(
            FormTemplate.id == template_id,
            FormTemplate.workspace_id == workspace_id,
            FormTemplate.is_deleted.is_(False),
        )
    )
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form template not found")
    return FormTemplateOut.model_validate(template)


@router.patch(
    "/{workspace_id}/forms/{template_id}",
    response_model=FormTemplateOut,
)
def update_form_template(
    workspace_id: UUID,
    template_id: UUID,
    payload: FormTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ws = _get_workspace_or_403(db, workspace_id, current_user)
    template = db.scalar(
        select(FormTemplate).where(
            FormTemplate.id == template_id,
            FormTemplate.workspace_id == workspace_id,
            FormTemplate.is_deleted.is_(False),
        )
    )
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form template not found")
    if payload.name is not None:
        template.name = payload.name
    if payload.description is not None:
        template.description = payload.description
    if payload.schema_ is not None:
        template.schema = payload.schema_
    if payload.active is not None:
        template.active = payload.active
    if payload.booking_type_id is not None:
        if payload.booking_type_id:
            bt = db.get(BookingType, payload.booking_type_id)
            if not bt or bt.workspace_id != workspace_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid booking_type_id")
        template.booking_type_id = payload.booking_type_id
    db.commit()
    db.refresh(template)
    return FormTemplateOut.model_validate(template)


@router.delete(
    "/{workspace_id}/forms/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_form_template(
    workspace_id: UUID,
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    _get_workspace_or_403(db, workspace_id, current_user)
    template = db.scalar(
        select(FormTemplate).where(
            FormTemplate.id == template_id,
            FormTemplate.workspace_id == workspace_id,
            FormTemplate.is_deleted.is_(False),
        )
    )
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form template not found")
    template.is_deleted = True
    db.commit()
    return None
