# app/services/public_booking_service.py
from __future__ import annotations

from datetime import datetime, date, timezone, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status, BackgroundTasks
from psycopg2.extras import DateTimeTZRange
from sqlalchemy import select, or_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.workspace import Workspace, WorkspaceStatus
from app.models.booking_type import BookingType
from app.models.availability_slot import AvailabilitySlot
from app.models.booking import Booking, BookingStatus, BookingSource
from app.models.contact import Contact
from app.models.conversation import Conversation, ConversationStatus, ChannelPreference
from app.models.message import Message, MessageChannel, MessageDirection, MessageStatus
from app.models.event_log import EventLog, ActorType
from app.models.form_template import FormTemplate
from app.schemas.booking import (
    PublicBookingTypeOut,
    PublicAvailabilitySlotOut,
    PublicBookingCreateRequest,
    PublicBookingOut,
    PublicBookingResponse,
)

# if/when you implement Resend integration:
#from app.integrations.email_resend import send_booking_confirmation_email


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _truncate_to_seconds(dt: datetime) -> datetime:
    """Truncate to whole seconds so JSON/DB rounding doesn't break equality."""
    return dt.replace(microsecond=0)


class PublicBookingService:
    def __init__(self, db: Session):
        self.db = db

    # ---------- Public API ----------

    def list_booking_types(self, workspace_id: UUID) -> List[PublicBookingTypeOut]:
        workspace = self._get_active_workspace(workspace_id)

        types = self.db.scalars(
            select(BookingType)
            .where(
                BookingType.workspace_id == workspace.id,
                BookingType.is_deleted.is_(False),
            )
            .order_by(BookingType.name)
        ).all()

        return [PublicBookingTypeOut.model_validate(t) for t in types]

    def get_availability_for_date(
        self,
        workspace_id: UUID,
        booking_type_slug: str,
        day: date,
    ) -> List[PublicAvailabilitySlotOut]:
        workspace = self._get_active_workspace(workspace_id)

        bt = self._get_booking_type_by_slug(workspace.id, booking_type_slug)

        day_start = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)

        slots = self.db.scalars(
            select(AvailabilitySlot)
            .where(
                AvailabilitySlot.workspace_id == workspace.id,
                AvailabilitySlot.booking_type_id == bt.id,
                AvailabilitySlot.start_at >= day_start,
                AvailabilitySlot.end_at <= day_end,
            )
            .order_by(AvailabilitySlot.start_at)
        ).all()

        if not slots:
            return []

        # Preload existing bookings overlapping these slots to mark availability
        slot_ranges = [(s.start_at, s.end_at) for s in slots]

        min_start = min(r[0] for r in slot_ranges)
        max_end = max(r[1] for r in slot_ranges)

        bookings = self.db.scalars(
            select(Booking)
            .where(
                Booking.workspace_id == workspace.id,
                Booking.booking_type_id == bt.id,
                Booking.status != BookingStatus.cancelled,
                Booking.start_at < max_end,
                Booking.end_at > min_start,
            )
        ).all()

        def slot_is_occupied(slot: AvailabilitySlot) -> bool:
            for b in bookings:
                same_staff = b.assigned_staff_id == slot.staff_user_id
                # if slot has no staff, treat any overlapping booking of this type as occupying
                if slot.staff_user_id is None:
                    if not (
                        b.end_at <= slot.start_at or b.start_at >= slot.end_at
                    ):
                        return True
                else:
                    if same_staff and not (
                        b.end_at <= slot.start_at or b.start_at >= slot.end_at
                    ):
                        return True
            return False

        result: List[PublicAvailabilitySlotOut] = []
        for s in slots:
            result.append(
                PublicAvailabilitySlotOut(
                    slot_start=_ensure_utc(s.start_at),
                    slot_end=_ensure_utc(s.end_at),
                    staff_name=s.staff_user.full_name if s.staff_user else None,
                    is_available=not slot_is_occupied(s),
                )
            )
        return result

    def get_available_dates_in_range(
        self,
        workspace_id: UUID,
        booking_type_slug: str,
        from_date: date,
        to_date: date,
    ) -> List[date]:
        """
        Returns dates in [from_date, to_date] that have at least one available slot.
        Used by the booking page to show a month calendar.
        """
        out: List[date] = []
        d = from_date
        while d <= to_date:
            slots = self.get_availability_for_date(workspace_id, booking_type_slug, d)
            if any(s.is_available for s in slots):
                out.append(d)
            d += timedelta(days=1)
        return out

    def create_public_booking(
        self,
        workspace_id: UUID,
        data: PublicBookingCreateRequest,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> PublicBookingResponse:
        workspace = self._get_active_workspace(workspace_id)
        bt = self._get_booking_type_by_slug(workspace.id, data.booking_type_slug)

        start_at = _ensure_utc(data.start_at)
        end_at = _ensure_utc(data.end_at)

        if end_at <= start_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="end_at must be after start_at.",
            )

        # Find an availability slot that contains the requested time. Match in Python with
        # UTC normalization and second truncation so JSON/DB datetime differences don't break.
        day_start_utc = datetime.combine(start_at.date(), datetime.min.time(), tzinfo=timezone.utc)
        day_end_utc = day_start_utc + timedelta(days=1)
        candidates = self.db.scalars(
            select(AvailabilitySlot)
            .where(
                AvailabilitySlot.workspace_id == workspace.id,
                AvailabilitySlot.booking_type_id == bt.id,
                AvailabilitySlot.start_at < day_end_utc,
                AvailabilitySlot.end_at > day_start_utc,
            )
            .order_by(AvailabilitySlot.start_at)
        ).all()
        req_start = _truncate_to_seconds(_ensure_utc(start_at))
        req_end = _truncate_to_seconds(_ensure_utc(end_at))
        slot = None
        for s in candidates:
            slot_start = _truncate_to_seconds(_ensure_utc(s.start_at))
            slot_end = _truncate_to_seconds(_ensure_utc(s.end_at))
            if slot_start <= req_start and slot_end >= req_end:
                slot = s
                break
        if not slot:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Requested time is not available for this booking type.",
            )

        contact = self._get_or_create_contact(workspace.id, data)
        conversation = self._get_or_create_conversation(workspace.id, contact)

        # Double-booking pre-check for staff-less slots
        if slot.staff_user_id is None:
            exists_conflict = self.db.scalar(
                select(func.count()).select_from(Booking).where(
                    Booking.workspace_id == workspace.id,
                    Booking.booking_type_id == bt.id,
                    Booking.status != BookingStatus.cancelled,
                    Booking.start_at < end_at,
                    Booking.end_at > start_at,
                )
            )
            if exists_conflict:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Time slot already booked.",
                )

        booking = Booking(
            workspace_id=workspace.id,
            contact_id=contact.id,
            booking_type_id=bt.id,
            assigned_staff_id=slot.staff_user_id,
            conversation_id=conversation.id,
            start_at=start_at,
            end_at=end_at,
            # PostgreSQL tstzrange expects a range type, not a plain record/tuple
            time_range=DateTimeTZRange(start_at, end_at, "[]"),
            status=BookingStatus.confirmed,
            source=BookingSource.public_page,
        )
        self.db.add(booking)

        # Queue confirmation email (and create Message row)
        # NOTE: Temporarily disabled to avoid DB NOT NULL violations on messages.conversation_id.
        # Public bookings will still be created; email sending can be wired later in a safer way.
        message_channel: Optional[MessageChannel] = None
        # if data.email:
        #     msg = self._create_outbound_message_email(
        #         workspace_id=workspace.id,
        #         conversation_id=conversation.id,
        #         to_email=data.email,
        #         booking=booking,
        #     )
        #     message_channel = msg.channel
        #     if background_tasks:
        #         self._enqueue_confirmation_email(background_tasks, workspace, contact, booking)

        # Link active forms for this workspace
        forms = self._get_active_forms_for_workspace(workspace.id)

        # Log events before commit
        self._log_event(
            workspace_id=workspace.id,
            event_type="booking.created",
            entity_type="booking",
            entity_id=str(booking.id),
            actor_type=ActorType.contact,
            actor_id=str(contact.id),
            payload={
                "booking_type_slug": bt.slug,
                "start_at": start_at.isoformat(),
                "end_at": end_at.isoformat(),
            },
        )
        if forms:
            self._log_event(
                workspace_id=workspace.id,
                event_type="booking.forms_linked",
                entity_type="booking",
                entity_id=str(booking.id),
                actor_type=ActorType.system,
                payload={
                    "form_template_ids": [str(f.id) for f in forms],
                },
            )

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            # Rely on constraint name to detect double booking
            if "excl_booking_per_staff_time" in str(exc.orig):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Time slot already booked.",
                )
            raise

        self.db.refresh(booking)

        return PublicBookingResponse(
            booking=PublicBookingOut.model_validate(booking),
            message_channel=message_channel,
        )

    # ---------- Internals ----------

    def _get_active_workspace(self, workspace_id: UUID) -> Workspace:
        ws = self.db.scalar(
            select(Workspace).where(
                Workspace.id == workspace_id,
                Workspace.status == WorkspaceStatus.active,
            )
        )
        if not ws:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found or not active.",
            )
        return ws

    def _get_booking_type_by_slug(
        self, workspace_id: UUID, slug: str
    ) -> BookingType:
        bt = self.db.scalar(
            select(BookingType).where(
                BookingType.workspace_id == workspace_id,
                BookingType.slug == slug,
                BookingType.is_deleted.is_(False),
            )
        )
        if not bt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking type not found.",
            )
        return bt

    def _get_or_create_contact(
        self, workspace_id: UUID, data: PublicBookingCreateRequest
    ) -> Contact:
        q = select(Contact).where(
            Contact.workspace_id == workspace_id,
            Contact.is_deleted.is_(False),
        )
        if data.email and data.phone:
            q = q.where(
                or_(
                    Contact.primary_email == data.email,
                    Contact.primary_phone == data.phone,
                )
            )
        elif data.email:
            q = q.where(Contact.primary_email == data.email)
        else:
            q = q.where(Contact.primary_phone == data.phone)

        contact = self.db.scalar(q)

        if contact:
            return contact

        contact = Contact(
            workspace_id=workspace_id,
            full_name=data.full_name,
            primary_email=data.email,
            primary_phone=data.phone,
        )
        self.db.add(contact)
        # Ensure the contact gets a primary key before it's used by Conversation
        self.db.flush()
        self._log_event(
            workspace_id=workspace_id,
            event_type="contact.created",
            entity_type="contact",
            entity_id=str(contact.id),
            actor_type=ActorType.contact,
        )
        return contact

    def _get_or_create_conversation(
        self, workspace_id: UUID, contact: Contact
    ) -> Conversation:
        conv = self.db.scalar(
            select(Conversation).where(
                Conversation.workspace_id == workspace_id,
                Conversation.contact_id == contact.id,
                Conversation.is_deleted.is_(False),
            )
        )
        if conv:
            return conv

        preferred = ChannelPreference.mixed
        if contact.primary_email and not contact.primary_phone:
            preferred = ChannelPreference.email
        elif contact.primary_phone and not contact.primary_email:
            preferred = ChannelPreference.sms

        conv = Conversation(
            workspace_id=workspace_id,
            contact_id=contact.id,
            status=ConversationStatus.open,
            channel_preference=preferred,
        )
        self.db.add(conv)
        self._log_event(
            workspace_id=workspace_id,
            event_type="conversation.opened",
            entity_type="conversation",
            entity_id=str(conv.id),
            actor_type=ActorType.contact,
            actor_id=str(contact.id),
        )
        return conv

    def _create_outbound_message_email(
        self,
        workspace_id: UUID,
        conversation_id: UUID,
        to_email: str,
        booking: Booking,
    ) -> Message:
        subject = f"Booking confirmation for {booking.start_at.date().isoformat()}"
        body_text = (
            f"Your booking is confirmed for {booking.start_at.isoformat()} "
            f"to {booking.end_at.isoformat()}."
        )

        msg = Message(
            workspace_id=workspace_id,
            conversation_id=conversation_id,
            direction=MessageDirection.outbound,
            channel=MessageChannel.email,
            subject=subject,
            body_text=body_text,
            body_html=None,
            from_address=None,  # filled by email integration using workspace config
            to_address=to_email,
            status=MessageStatus.queued,
        )
        self.db.add(msg)

        self._log_event(
            workspace_id=workspace_id,
            event_type="message.queued",
            entity_type="message",
            entity_id=str(msg.id),
            actor_type=ActorType.system,
            payload={"channel": "email"},
        )
        return msg

    def _get_active_forms_for_workspace(
        self, workspace_id: UUID
    ) -> List[FormTemplate]:
        return self.db.scalars(
            select(FormTemplate).where(
                FormTemplate.workspace_id == workspace_id,
                FormTemplate.is_deleted.is_(False),
                FormTemplate.active.is_(True),
            )
        ).all()

    def _enqueue_confirmation_email(
        self,
        background_tasks: BackgroundTasks,
        workspace: Workspace,
        contact: Contact,
        booking: Booking,
    ) -> None:
        # Example hook into email integration layer.
        # Implement send_booking_confirmation_email(...) separately.
        if not contact.primary_email:
            return

        # background_tasks.add_task(
        #     send_booking_confirmation_email,
        #     workspace_id=str(workspace.id),
        #     to_email=contact.primary_email,
        #     booking_id=str(booking.id),
        # )
        pass

    def _log_event(
        self,
        workspace_id: UUID,
        event_type: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        actor_type: ActorType = ActorType.system,
        actor_id: Optional[str] = None,
        payload: Optional[dict] = None,
    ) -> None:
        ev = EventLog(
            workspace_id=workspace_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_type=actor_type,
            actor_id=actor_id,
            payload=payload or {},
        )
        self.db.add(ev)