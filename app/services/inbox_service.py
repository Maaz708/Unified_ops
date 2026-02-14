# app/services/inbox_service.py
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List
from uuid import UUID

from fastapi import HTTPException, status, BackgroundTasks
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session

from app.models.contact import Contact
from app.models.conversation import (
    Conversation,
    ConversationStatus,
    ChannelPreference,
)
from app.models.message import (
    Message,
    MessageChannel,
    MessageDirection,
    MessageStatus,
)
from app.models.event_log import EventLog, ActorType
from app.schemas.message import (
    StaffSendMessageRequest,
    InboundMessageWebhook,
    MessageOut,
)
from app.core.database import SessionLocal
from app.services.communication_service import CommunicationService


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _send_outbound_in_background(message_id: UUID) -> None:
    """Run send_outbound_message in a fresh DB session so status updates are committed."""
    from loguru import logger

    db = SessionLocal()
    try:
        msg = db.get(Message, message_id)
        if not msg:
            logger.warning("Inbox background send: message not found message_id={}", message_id)
            return
        logger.info("Inbox background send: sending message_id={} to={}", message_id, msg.to_address)
        CommunicationService(db).send_outbound_message(msg)
        db.commit()
    except Exception as exc:
        logger.exception("Inbox background send failed message_id={}: {}", message_id, exc)
        db.rollback()
        raise
    finally:
        db.close()




class InboxService:
    def __init__(self, db: Session):
        self.db = db
        self.comm = CommunicationService(db)

    # ---------- Public API ----------

    def send_message(
        self,
        workspace_id: UUID,
        staff_user_id: UUID,
        payload: StaffSendMessageRequest,
        background_tasks: BackgroundTasks | None = None,
    ) -> MessageOut:
        # Validate payload vs channel
        payload.validate_channel_payload()

        contact = self._get_contact_for_workspace(workspace_id, payload.contact_id)
        conv = self._get_or_create_conversation(workspace_id, contact)

        msg = Message(
            workspace_id=workspace_id,
            conversation_id=conv.id,
            direction=MessageDirection.outbound,
            channel=payload.channel,
            subject=payload.subject,
            body_text=payload.body,
            body_html=None,
            from_address=None,
            to_address=payload.to_email,
            from_phone=None,
            to_phone=payload.to_phone,
            status=MessageStatus.queued,
        )
        self.db.add(msg)

        # Update conversation state
        now = _utc_now()
        conv.last_message_at = now
        # Staff replies should pause automation
        conv.automation_paused = True
        conv.last_staff_reply_at = now

        self._log_event(
            workspace_id=workspace_id,
            event_type="message.queued",
            entity_type="message",
            entity_id=str(msg.id),
            actor_type=ActorType.staff,
            actor_id=str(staff_user_id),
            payload={
                "channel": payload.channel.value,
                "conversation_id": str(conv.id),
                "contact_id": str(contact.id),
            },
        )

        self._log_event(
            workspace_id=workspace_id,
            event_type="automation.paused",
            entity_type="conversation",
            entity_id=str(conv.id),
            actor_type=ActorType.staff,
            actor_id=str(staff_user_id),
        )

        # Background sending (use fresh session so sent status is committed)
        if background_tasks:
            # Commit first to ensure message exists when background task runs
            self.db.commit()
            self.db.refresh(msg)
            background_tasks.add_task(_send_outbound_in_background, msg.id)
        else:
            self.comm.send_outbound_message(msg)
            self.db.commit()
            self.db.refresh(msg)

        return MessageOut.model_validate(msg)

    def send_reply_by_conversation(
        self,
        workspace_id: UUID,
        staff_user_id: UUID,
        conversation_id: UUID,
        body: str,
        background_tasks: BackgroundTasks | None = None,
    ) -> MessageOut:
        """Send a reply from the inbox: look up conversation and contact, then send email (or SMS) to the contact."""
        conv = self.db.scalar(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.workspace_id == workspace_id,
                Conversation.is_deleted.is_(False),
            )
        )
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )
        contact = self.db.get(Contact, conv.contact_id)
        if not contact or contact.workspace_id != workspace_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found.",
            )
        channel = MessageChannel.email
        to_email = contact.primary_email
        to_phone = contact.primary_phone
        if to_email:
            channel = MessageChannel.email
        elif to_phone:
            channel = MessageChannel.sms
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contact has no email or phone; cannot send reply.",
            )
        payload = StaffSendMessageRequest(
            contact_id=str(contact.id),
            channel=channel,
            body=body,
            to_email=to_email,
            to_phone=to_phone,
        )
        return self.send_message(workspace_id, staff_user_id, payload, background_tasks)

    def receive_message(
        self,
        webhook: InboundMessageWebhook,
    ) -> None:
        """
        Called from email/SMS webhooks. No auth — authenticated by provider secrets.
        """
        workspace_id = UUID(webhook.workspace_id)

        contact = self._get_or_create_contact_from_inbound(workspace_id, webhook)
        conv = self._get_or_create_conversation(workspace_id, contact)

        msg = Message(
            workspace_id=workspace_id,
            conversation_id=conv.id,
            direction=MessageDirection.inbound,
            channel=webhook.channel,
            subject=webhook.subject,
            body_text=webhook.body,
            body_html=None,
            from_address=webhook.from_email,
            to_address=webhook.to_email,
            from_phone=webhook.from_phone,
            to_phone=webhook.to_phone,
            status=MessageStatus.delivered,
        )
        self.db.add(msg)

        conv.last_message_at = webhook.normalized_received_at()
        # Do NOT change automation_paused here; that is staff-driven.

        self._log_event(
            workspace_id=workspace_id,
            event_type="message.received",
            entity_type="message",
            entity_id=str(msg.id),
            actor_type=ActorType.contact,
            actor_id=str(contact.id),
            payload={"channel": webhook.channel.value},
        )

        # This event is the hook for automation engine to trigger workflows.
        self._log_event(
            workspace_id=workspace_id,
            event_type="conversation.inbound_activity",
            entity_type="conversation",
            entity_id=str(conv.id),
            actor_type=ActorType.contact,
            actor_id=str(contact.id),
        )

        self.db.commit()

    def pause_automation_on_reply(self, conversation_id: UUID) -> None:
        conv = self.db.get(Conversation, conversation_id)
        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )

        conv.automation_paused = True
        conv.last_staff_reply_at = _utc_now()

        self._log_event(
            workspace_id=conv.workspace_id,
            event_type="automation.paused",
            entity_type="conversation",
            entity_id=str(conv.id),
            actor_type=ActorType.system,
        )

        self.db.commit()

    def get_unanswered_inbound_conversations(
        self,
        workspace_id: UUID,
        min_age_minutes: int = 30,
        limit: int = 50,
    ) -> List[Conversation]:
        """
        Returns conversations where:
        - last message was INBOUND
        - no outbound reply after that
        - last inbound is older than min_age_minutes
        - conversation is open
        - automation is NOT paused
        """
        cutoff = _utc_now() - timedelta(minutes=min_age_minutes)

        # Subqueries for last inbound / outbound times
        last_inbound_subq = (
            select(
                Message.conversation_id,
                func.max(Message.created_at).label("last_inbound_at"),
            )
            .where(
                Message.workspace_id == workspace_id,
                Message.direction == MessageDirection.inbound,
            )
            .group_by(Message.conversation_id)
            .subquery()
        )

        last_outbound_subq = (
            select(
                Message.conversation_id,
                func.max(Message.created_at).label("last_outbound_at"),
            )
            .where(
                Message.workspace_id == workspace_id,
                Message.direction == MessageDirection.outbound,
            )
            .group_by(Message.conversation_id)
            .subquery()
        )

        q = (
            select(Conversation)
            .join(
                last_inbound_subq,
                last_inbound_subq.c.conversation_id == Conversation.id,
            )
            .outerjoin(
                last_outbound_subq,
                last_outbound_subq.c.conversation_id == Conversation.id,
            )
            .where(
                Conversation.workspace_id == workspace_id,
                Conversation.status == ConversationStatus.open,
                Conversation.automation_paused.is_(False),
                last_inbound_subq.c.last_inbound_at < cutoff,
                or_(
                    last_outbound_subq.c.last_outbound_at.is_(None),
                    last_outbound_subq.c.last_outbound_at
                    < last_inbound_subq.c.last_inbound_at,
                ),
            )
            .order_by(last_inbound_subq.c.last_inbound_at.asc())
            .limit(limit)
        )

        return self.db.scalars(q).all()

    # ---------- Internals ----------

    def _get_contact_for_workspace(
        self, workspace_id: UUID, contact_id: str
    ) -> Contact:
        contact = self.db.scalar(
            select(Contact).where(
                Contact.workspace_id == workspace_id,
                Contact.id == UUID(contact_id),
                Contact.is_deleted.is_(False),
            )
        )
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found in this workspace.",
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
            actor_type=ActorType.system,
            actor_id=str(contact.id),
        )
        return conv

    def _get_or_create_contact_from_inbound(
        self, workspace_id: UUID, webhook: InboundMessageWebhook
    ) -> Contact:
        q = select(Contact).where(
            Contact.workspace_id == workspace_id,
            Contact.is_deleted.is_(False),
        )
        if webhook.from_email:
            q = q.where(Contact.primary_email == webhook.from_email)
        elif webhook.from_phone:
            q = q.where(Contact.primary_phone == webhook.from_phone)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inbound message must include from_email or from_phone.",
            )

        contact = self.db.scalar(q)
        if contact:
            return contact

        contact = Contact(
            workspace_id=workspace_id,
            full_name=webhook.from_email or webhook.from_phone or "Unknown",
            primary_email=webhook.from_email,
            primary_phone=webhook.from_phone,
        )
        self.db.add(contact)

        self._log_event(
            workspace_id=workspace_id,
            event_type="contact.created",
            entity_type="contact",
            entity_id=str(contact.id),
            actor_type=ActorType.contact,
        )
        return contact

    def _log_event(
        self,
        workspace_id: UUID,
        event_type: str,
        entity_type: str | None = None,
        entity_id: str | None = None,
        actor_type: ActorType = ActorType.system,
        actor_id: str | None = None,
        payload: dict | None = None,
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