# app/api/routers/public_forms.py
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.dependencies.db import get_db
from app.models.workspace import Workspace, WorkspaceStatus
from app.models.form_template import FormTemplate
from app.models.form_submission import FormSubmission
from app.models.booking import Booking
from app.models.contact import Contact
from app.models.conversation import Conversation, ConversationStatus, ChannelPreference
from app.models.message import Message, MessageDirection, MessageChannel, MessageStatus
from app.models.event_log import EventLog, ActorType
from pydantic import BaseModel
from app.schemas.form import FormTemplateOut, FormSubmissionOut, PublicFormSubmitRequest, PublicContactRequest

router = APIRouter(prefix="/public", tags=["public-forms"])


class PublicContactResponse(BaseModel):
    contact_id: UUID
    conversation_id: UUID
    message: str = "We'll be in touch soon."


class BookingFormLinkOut(BaseModel):
    form_template_id: UUID | None
    form_name: str | None


def _get_active_workspace(db: Session, workspace_id: UUID) -> Workspace:
    ws = db.scalar(
        select(Workspace).where(
            Workspace.id == workspace_id,
            Workspace.status == WorkspaceStatus.active,
        )
    )
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found or not active")
    return ws


@router.get(
    "/{workspace_id}/bookings/{booking_id}/form-link",
    response_model=BookingFormLinkOut,
)
def get_booking_form_link(
    workspace_id: UUID,
    booking_id: UUID,
    db: Session = Depends(get_db),
):
    """Return the form template linked to this booking's type (if any). Used to send form link after booking."""
    _get_active_workspace(db, workspace_id)
    booking = db.scalar(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.workspace_id == workspace_id,
        )
    )
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    template = db.scalar(
        select(FormTemplate).where(
            FormTemplate.workspace_id == workspace_id,
            FormTemplate.booking_type_id == booking.booking_type_id,
            FormTemplate.is_deleted.is_(False),
            FormTemplate.active.is_(True),
        )
    )
    if not template:
        return BookingFormLinkOut(form_template_id=None, form_name=None)
    return BookingFormLinkOut(form_template_id=template.id, form_name=template.name)


@router.get(
    "/{workspace_id}/forms/{template_id}",
    response_model=FormTemplateOut,
)
def get_public_form_template(
    workspace_id: UUID,
    template_id: UUID,
    db: Session = Depends(get_db),
):
    """Return form template for public form completion page (no auth)."""
    _get_active_workspace(db, workspace_id)
    template = db.scalar(
        select(FormTemplate).where(
            FormTemplate.id == template_id,
            FormTemplate.workspace_id == workspace_id,
            FormTemplate.is_deleted.is_(False),
            FormTemplate.active.is_(True),
        )
    )
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")
    return FormTemplateOut.model_validate(template)


@router.post(
    "/{workspace_id}/forms/submit",
    response_model=FormSubmissionOut,
    status_code=status.HTTP_201_CREATED,
)
def submit_public_form(
    workspace_id: UUID,
    payload: PublicFormSubmitRequest,
    db: Session = Depends(get_db),
):
    """
    Submit a form for a booking. Validates that booking and contact belong to workspace and match.
    """
    ws = _get_active_workspace(db, workspace_id)
    template = db.scalar(
        select(FormTemplate).where(
            FormTemplate.id == payload.template_id,
            FormTemplate.workspace_id == workspace_id,
            FormTemplate.is_deleted.is_(False),
        )
    )
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form template not found")

    booking = db.scalar(
        select(Booking).where(
            Booking.id == payload.booking_id,
            Booking.workspace_id == workspace_id,
            Booking.contact_id == payload.contact_id,
        )
    )
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking not found or does not match contact",
        )

    # Avoid duplicate submission for same form+booking
    existing = db.scalar(
        select(FormSubmission).where(
            FormSubmission.form_template_id == payload.template_id,
            FormSubmission.booking_id == payload.booking_id,
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Form already submitted for this booking",
        )

    submitted_at = datetime.now(timezone.utc)
    submission = FormSubmission(
        workspace_id=ws.id,
        form_template_id=template.id,
        booking_id=booking.id,
        contact_id=payload.contact_id,
        submitted_at=submitted_at,
        answers=payload.answers or {},
    )
    db.add(submission)
    db.flush()

    ev = EventLog(
        workspace_id=ws.id,
        event_type="form.submitted",
        entity_type="form_submission",
        entity_id=str(submission.id),
        actor_type=ActorType.contact,
        actor_id=str(payload.contact_id),
        payload={"form_template_id": str(payload.template_id), "booking_id": str(payload.booking_id)},
    )
    db.add(ev)

    # Create an inbox message so owner can see form content and reply
    contact = db.get(Contact, payload.contact_id)
    if contact:
        conv = db.scalar(
            select(Conversation).where(
                Conversation.workspace_id == workspace_id,
                Conversation.contact_id == contact.id,
                Conversation.is_deleted.is_(False),
            )
        )
        if not conv:
            preferred = ChannelPreference.mixed
            if contact.primary_email and not contact.primary_phone:
                preferred = ChannelPreference.email
            elif contact.primary_phone and not contact.primary_email:
                preferred = ChannelPreference.sms
            conv = Conversation(
                workspace_id=ws.id,
                contact_id=contact.id,
                status=ConversationStatus.open,
                channel_preference=preferred,
            )
            db.add(conv)
            db.flush()

        # Format form answers as readable text for inbox - show only customer's actual response
        answers = payload.answers or {}
        schema_fields = (template.schema or {}).get("fields") or []

        # Look for a message/notes field first, otherwise show first text field
        customer_message = None

        # Priority 1: Look for common message field names
        message_fields = ['message', 'notes', 'special_requests', 'comments', 'additional_info']
        for field_name in message_fields:
            if field_name in answers and answers[field_name]:
                customer_message = answers[field_name]
                break

        # Priority 2: If no message field, find first text field
        if not customer_message:
            for field in schema_fields:
                if isinstance(field, dict):
                    field_id = field.get("id")
                    field_type = field.get("type", "")
                    if field_id in answers and field_type in ["text", "textarea"]:
                        customer_message = answers[field_id]
                        break

        # Format the inbox message
        if customer_message:
            body_text = f"{customer_message}"
        else:
            # Fallback: show minimal info if no message found
            body_text = f"Form submitted: {template.name}"

        inbox_msg = Message(
            workspace_id=ws.id,
            conversation_id=conv.id,
            direction=MessageDirection.inbound,
            channel=MessageChannel.email,
            subject=f"Form: {template.name}",
            body_text=body_text,
            body_html=None,
            from_address=contact.primary_email,
            to_address=None,
            status=MessageStatus.delivered,
        )
        db.add(inbox_msg)
        now = datetime.now(timezone.utc)
        conv.last_message_at = now

    db.commit()
    db.refresh(submission)
    return FormSubmissionOut.model_validate(submission)


@router.post(
    "/{workspace_id}/contact",
    response_model=PublicContactResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_public_contact(
    workspace_id: UUID,
    payload: PublicContactRequest,
    db: Session = Depends(get_db),
):
    """
    Public contact form: create contact, open conversation, optionally add first message.
    """
    ws = _get_active_workspace(db, workspace_id)
    if not payload.email and not payload.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of email or phone is required",
        )

    # Match existing contact by email or phone
    contact = None
    if payload.email:
        contact = db.scalar(
            select(Contact).where(
                Contact.workspace_id == workspace_id,
                Contact.primary_email == payload.email,
                Contact.is_deleted.is_(False),
            )
        )
    if not contact and payload.phone:
        contact = db.scalar(
            select(Contact).where(
                Contact.workspace_id == workspace_id,
                Contact.primary_phone == payload.phone,
                Contact.is_deleted.is_(False),
            )
        )

    if not contact:
        contact = Contact(
            workspace_id=ws.id,
            full_name=payload.name,
            primary_email=payload.email,
            primary_phone=payload.phone,
        )
        db.add(contact)
        db.flush()
        ev = EventLog(
            workspace_id=ws.id,
            event_type="contact.created",
            entity_type="contact",
            entity_id=str(contact.id),
            actor_type=ActorType.contact,
        )
        db.add(ev)
    else:
        if payload.name and contact.full_name != payload.name:
            contact.full_name = payload.name
        if payload.email and not contact.primary_email:
            contact.primary_email = payload.email
        if payload.phone and not contact.primary_phone:
            contact.primary_phone = payload.phone

    conversation = db.scalar(
        select(Conversation).where(
            Conversation.workspace_id == workspace_id,
            Conversation.contact_id == contact.id,
            Conversation.is_deleted.is_(False),
        )
    )
    if not conversation:
        preferred = ChannelPreference.mixed
        if contact.primary_email and not contact.primary_phone:
            preferred = ChannelPreference.email
        elif contact.primary_phone and not contact.primary_email:
            preferred = ChannelPreference.sms
        conversation = Conversation(
            workspace_id=ws.id,
            contact_id=contact.id,
            status=ConversationStatus.open,
            channel_preference=preferred,
        )
        db.add(conversation)
        db.flush()
        ev = EventLog(
            workspace_id=ws.id,
            event_type="conversation.opened",
            entity_type="conversation",
            entity_id=str(conversation.id),
            actor_type=ActorType.contact,
            actor_id=str(contact.id),
        )
        db.add(ev)

    if payload.message:
        msg = Message(
            workspace_id=ws.id,
            conversation_id=conversation.id,
            direction=MessageDirection.inbound,
            channel=MessageChannel.email,
            subject=None,
            body_text=payload.message,
            body_html=None,
            from_address=contact.primary_email,
            to_address=None,
            status=MessageStatus.delivered,
        )
        db.add(msg)

    db.commit()
    db.refresh(contact)
    db.refresh(conversation)
    return PublicContactResponse(
        contact_id=contact.id,
        conversation_id=conversation.id,
        message="We'll be in touch soon.",
    )
