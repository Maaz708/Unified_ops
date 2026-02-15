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
        print(f"DEBUG: get_availability_for_date called for workspace {workspace_id}, slug {booking_type_slug}, day {day}")
        
        workspace = self._get_active_workspace(workspace_id)

        bt = self._get_booking_type_by_slug(workspace.id, booking_type_slug)
        print(f"DEBUG: Found booking type: {bt.name} (ID: {bt.id})")

        day_start = datetime.combine(day, datetime.min.time())  # No timezone - match database
        day_end = day_start + timedelta(days=1)
        print(f"DEBUG: Searching slots between {day_start} and {day_end}")
        print(f"DEBUG: Day start timezone: {day_start.tzinfo}")
        print(f"DEBUG: Current UTC time: {datetime.now(timezone.utc)}")

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
        
        print(f"DEBUG: Found {len(slots)} availability slots for {day}")
        for i, s in enumerate(slots):
            print(f"  {i+1}. {s.start_at} - {s.end_at} (staff: {s.staff_user_id})")

        if not slots:
            print("DEBUG: No availability slots found, returning empty list")
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
        
        print(f"DEBUG: Availability check for {day}, found {len(bookings)} bookings:")
        for i, b in enumerate(bookings):
            print(f"  {i+1}. {b.start_at} - {b.end_at} ({b.status})")

        def slot_is_occupied(slot: AvailabilitySlot) -> bool:
            for b in bookings:
                same_staff = b.assigned_staff_id == slot.staff_user_id
                # Compare database times directly (no UTC conversion needed)
                
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
            # Split large slots into 1-hour chunks
            current_start = s.start_at
            slot_duration = (s.end_at - s.start_at).total_seconds() / 3600  # hours
            
            # Create 1-hour slots
            while current_start + timedelta(hours=1) <= s.end_at:
                hour_slot_end = current_start + timedelta(hours=1)
                
                # Check if this specific hour is occupied
                hour_slot_occupied = False
                for b in bookings:
                    if (b.status != BookingStatus.cancelled):
                        # Compare database times directly (no UTC conversion needed)
                        
                        if not (b.end_at <= current_start or b.start_at >= hour_slot_end):
                            same_staff = b.assigned_staff_id == s.staff_user_id
                            if s.staff_user_id is None or same_staff:
                                hour_slot_occupied = True
                                break
                
                result.append(
                    PublicAvailabilitySlotOut(
                        slot_start=current_start,  # Keep database time, don't convert to UTC
                        slot_end=hour_slot_end,     # Keep database time, don't convert to UTC
                        staff_name=s.staff_user.full_name if s.staff_user else None,
                        is_available=not hour_slot_occupied,
                    )
                )
                print(f"DEBUG: Created slot {current_start} - {hour_slot_end}, available: {not hour_slot_occupied}")
                current_start = hour_slot_end
            
            # Handle remaining partial hour if any
            if current_start < s.end_at:
                # Check if this remaining slot is occupied
                remaining_occupied = False
                for b in bookings:
                    if (b.status != BookingStatus.cancelled):
                        # Compare database times directly (no UTC conversion needed)
                        
                        if not (b.end_at <= current_start or b.start_at >= s.end_at):
                            same_staff = b.assigned_staff_id == s.staff_user_id
                            if s.staff_user_id is None or same_staff:
                                remaining_occupied = True
                                break
                
                result.append(
                    PublicAvailabilitySlotOut(
                        slot_start=current_start,  # Keep database time, don't convert to UTC
                        slot_end=s.end_at,         # Keep database time, don't convert to UTC
                        staff_name=s.staff_user.full_name if s.staff_user else None,
                        is_available=not remaining_occupied,
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

        start_at = data.start_at
        end_at = data.end_at
        
        # Convert UTC times from frontend to database naive times
        if start_at.tzinfo is not None:
            start_at = start_at.replace(tzinfo=None)
        if end_at.tzinfo is not None:
            end_at = end_at.replace(tzinfo=None)
        
        # Debug logging
        print(f"DEBUG: Received booking request:")
        print(f"  Raw start_at: {data.start_at}")
        print(f"  Raw end_at: {data.end_at}")
        print(f"  Parsed start_at: {start_at}")
        print(f"  Parsed end_at: {end_at}")

        if end_at <= start_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="end_at must be after start_at.",
            )

        # Validate booking duration (max 2 hours)
        duration_hours = (end_at - start_at).total_seconds() / 3600
        if duration_hours > 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking duration cannot exceed 2 hours.",
            )

        # Check if the requested time conflicts with existing bookings
        print(f"DEBUG: Checking for conflicts between {start_at} and {end_at}")
        
        # First, let's see all bookings for this workspace and type
        all_bookings = self.db.scalars(
            select(Booking)
            .where(
                Booking.workspace_id == workspace.id,
                Booking.booking_type_id == bt.id,
                Booking.status != BookingStatus.cancelled,
            )
            .order_by(Booking.start_at)
        ).all()
        
        print(f"DEBUG: Found {len(all_bookings)} total bookings:")
        for i, b in enumerate(all_bookings):
            # Compare database times directly (no UTC conversion needed)
            print(f"  {i+1}. {b.start_at} - {b.end_at} ({b.status})")
            # Check overlap using database times
            overlap = (b.start_at < end_at and b.end_at > start_at)
            print(f"     Overlap with request: {overlap}")
        
        # Find conflicting booking using database time comparison
        conflicting_booking = None
        for b in all_bookings:
            overlap = (b.start_at < end_at and b.end_at > start_at)
            if overlap:
                conflicting_booking = b
                break
        
        if conflicting_booking:
            print(f"DEBUG: Found conflicting booking: {conflicting_booking.start_at} - {conflicting_booking.end_at} ({conflicting_booking.status})")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Time slot already booked.",
            )
        else:
            print("DEBUG: No conflicting booking found")

        contact = self._get_or_create_contact(workspace.id, data)
        conversation = self._get_or_create_conversation(workspace.id, contact)

        booking = Booking(
            workspace_id=workspace.id,
            contact_id=contact.id,
            booking_type_id=bt.id,
            assigned_staff_id=None,  # No specific staff assignment for public bookings
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