# app/services/automation_service.py
from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.automation_rule import AutomationRule
from app.models.automation_run import AutomationRun, AutomationRunStatus
from app.models.event_log import EventLog, ActorType
from app.models.contact import Contact
from app.models.conversation import Conversation, ConversationStatus, ChannelPreference
from app.models.booking import Booking
from app.models.form_template import FormTemplate
from app.models.alert import Alert, AlertSeverity, AlertSource
from app.models.message import (
    Message,
    MessageChannel,
    MessageDirection,
    MessageStatus,
)
from app.services.communication_service import CommunicationService


class AutomationService:
    """
    Event-based automation engine.

    - handle_event(event, background_tasks?)
    - executes AutomationRule.actions for matching rules
    - all actions are explicit in rule JSON
    """

    def __init__(self, db: Session):
        self.db = db
        self.comm = CommunicationService(db)

    # ---------- ENTRYPOINT ----------

    def handle_event(
        self,
        event: EventLog,
        background_tasks: BackgroundTasks | None = None,
    ) -> None:
        rules = self._get_matching_rules(event)
        if not rules:
            return

        for rule in rules:
            run = AutomationRun(
                workspace_id=event.workspace_id,
                rule_id=rule.id,
                event_id=event.id,
                status=AutomationRunStatus.pending,
            )
            self.db.add(run)
            self.db.flush()

            if background_tasks:
                background_tasks.add_task(self.execute_run, run.id)
            else:
                # synchronous (mainly for tests / simple flows)
                self.execute_run(run.id)

    # ---------- EXECUTION ----------

    def execute_run(self, run_id: UUID) -> None:
        run = self.db.get(AutomationRun, run_id)
        if not run:
            return

        event = run.event
        rule = run.rule

        run.status = AutomationRunStatus.running
        self.db.flush()

        try:
            # Optional: conditions filter on event.payload, entity, actor
            if not self._conditions_match(rule.conditions or {}, event):
                run.status = AutomationRunStatus.skipped
                self.db.flush()
                return

            results: list[dict[str, Any]] = []
            for action in rule.actions.get("steps", []):
                result = self._execute_action(action, event)
                results.append({"action": action, "result": result})

            run.status = AutomationRunStatus.succeeded
            run.metadata = {"results": results}

            self._log_automation_event(
                event.workspace_id,
                "automation.run_succeeded",
                run=run,
            )
        except Exception as exc:  # noqa: BLE001
            run.status = AutomationRunStatus.failed
            run.error_message = str(exc)

            self._log_automation_event(
                event.workspace_id,
                "automation.run_failed",
                run=run,
            )
        finally:
            self.db.commit()

    # ---------- Rule selection & condition evaluation ----------

    def _get_matching_rules(self, event: EventLog) -> list[AutomationRule]:
        return self.db.scalars(
            select(AutomationRule).where(
                AutomationRule.workspace_id == event.workspace_id,
                AutomationRule.is_deleted.is_(False),
                AutomationRule.is_active.is_(True),
                AutomationRule.event_type == event.event_type,
            )
        ).all()

    def _conditions_match(self, conditions: dict, event: EventLog) -> bool:
        """
        Minimal, explicit filter:
        - payload_equals: dict of key->value equals checks on event.payload
        - actor_type_in: list of allowed actor types
        """
        payload = event.payload or {}

        payload_equals = conditions.get("payload_equals") or {}
        for key, expected in payload_equals.items():
            if payload.get(key) != expected:
                return False

        actor_type_in = conditions.get("actor_type_in")
        if actor_type_in and event.actor_type.value not in actor_type_in:
            return False

        return True

    # ---------- Action execution ----------

    def _execute_action(self, action: dict, event: EventLog) -> dict:
        """
        Supported action types:

        - send_welcome_message
        - send_booking_confirmation
        - send_booking_reminder
        - send_form_reminder
        - raise_inventory_alert   (for extra handling on top of base alert)
        - pause_automation_for_conversation
        """
        action_type = action.get("type")

        if action_type == "send_welcome_message":
            return self._act_send_welcome_message(action, event)
        if action_type == "send_booking_confirmation":
            return self._act_send_booking_confirmation(action, event)
        if action_type == "send_booking_reminder":
            return self._act_send_booking_reminder(action, event)
        if action_type == "send_form_reminder":
            return self._act_send_form_reminder(action, event)
        if action_type == "raise_inventory_alert":
            return self._act_raise_inventory_alert(action, event)
        if action_type == "pause_automation_for_conversation":
            return self._act_pause_automation_for_conversation(action, event)

        # Unknown action: explicit no-op with metadata
        return {"status": "ignored", "reason": "unknown_action_type"}

    # ----- Action implementations -----

    def _act_send_welcome_message(self, action: dict, event: EventLog) -> dict:
        """
        Trigger: event_type = 'contact.created'
        Action JSON example:
        {
          "type": "send_welcome_message",
          "channel": "email",
          "subject_template": "Welcome to {{workspace_name}}",
          "body_template": "Hi {{contact_name}}, ...",
        }
        """
        channel = MessageChannel(action.get("channel", "email"))

        contact = self._get_contact_from_event(event)
        conv = self._get_or_create_conversation(event.workspace_id, contact)

        subject = action.get("subject_template", "Welcome!")
        body = action.get("body_template", "Welcome to our service.")

        msg = Message(
            workspace_id=event.workspace_id,
            conversation_id=conv.id,
            direction=MessageDirection.outbound,
            channel=channel,
            subject=subject if channel == MessageChannel.email else None,
            body_text=body,
            body_html=None,
            to_address=contact.primary_email if channel == MessageChannel.email else None,
            to_phone=contact.primary_phone
            if channel == MessageChannel.sms
            else None,
            status=MessageStatus.queued,
        )
        self.db.add(msg)
        self.comm.send_outbound_message(msg)

        return {"status": "sent", "message_id": str(msg.id)}

    def _act_send_booking_confirmation(self, action: dict, event: EventLog) -> dict:
        """
        Trigger: event_type = 'booking.created'
        """
        booking = self._get_booking_from_event(event)
        contact = booking.contact
        conv = booking.conversation

        channel = MessageChannel(action.get("channel", "email"))
        subject = action.get(
            "subject_template", "Your booking is confirmed"
        )
        body = action.get(
            "body_template",
            f"Your booking is confirmed for {booking.start_at.isoformat()}",
        )

        msg = Message(
            workspace_id=event.workspace_id,
            conversation_id=conv.id,
            direction=MessageDirection.outbound,
            channel=channel,
            subject=subject if channel == MessageChannel.email else None,
            body_text=body,
            body_html=None,
            to_address=contact.primary_email if channel == MessageChannel.email else None,
            to_phone=contact.primary_phone
            if channel == MessageChannel.sms
            else None,
            status=MessageStatus.queued,
        )
        self.db.add(msg)
        self.comm.send_outbound_message(msg)
        return {"status": "sent", "message_id": str(msg.id)}

    def _act_send_booking_reminder(self, action: dict, event: EventLog) -> dict:
        """
        Trigger: event_type = 'booking.reminder_due' (emitted by a scheduler)
        """
        booking = self._get_booking_from_event(event)
        contact = booking.contact
        channel = MessageChannel(action.get("channel", "email"))
        subject = action.get(
            "subject_template", "Upcoming booking reminder"
        )
        body = action.get(
            "body_template",
            f"Reminder: your booking is at {booking.start_at.isoformat()}",
        )

        conv = booking.conversation
        msg = Message(
            workspace_id=event.workspace_id,
            conversation_id=conv.id,
            direction=MessageDirection.outbound,
            channel=channel,
            subject=subject if channel == MessageChannel.email else None,
            body_text=body,
            body_html=None,
            to_address=contact.primary_email if channel == MessageChannel.email else None,
            to_phone=contact.primary_phone
            if channel == MessageChannel.sms
            else None,
            status=MessageStatus.queued,
        )
        self.db.add(msg)
        self.comm.send_outbound_message(msg)
        return {"status": "sent", "message_id": str(msg.id)}

    def _act_send_form_reminder(self, action: dict, event: EventLog) -> dict:
        """
        Trigger: event_type = 'form.pending_reminder_due',
        payload contains booking_id, contact_id etc.
        """
        booking = self._get_booking_from_event(event)
        contact = booking.contact
        channel = MessageChannel(action.get("channel", "email"))
        subject = action.get("subject_template", "Form reminder")
        body = action.get(
            "body_template",
            "Please complete your post-booking form.",
        )

        conv = booking.conversation
        msg = Message(
            workspace_id=event.workspace_id,
            conversation_id=conv.id,
            direction=MessageDirection.outbound,
            channel=channel,
            subject=subject if channel == MessageChannel.email else None,
            body_text=body,
            body_html=None,
            to_address=contact.primary_email if channel == MessageChannel.email else None,
            to_phone=contact.primary_phone
            if channel == MessageChannel.sms
            else None,
            status=MessageStatus.queued,
        )
        self.db.add(msg)
        self.comm.send_outbound_message(msg)
        return {"status": "sent", "message_id": str(msg.id)}

    def _act_raise_inventory_alert(self, action: dict, event: EventLog) -> dict:
        """
        Trigger: event_type = 'inventory.low_stock'
        (InventoryService already logs this event; this rule can do extra work
         like escalating severity or sending additional notifications.)
        """
        payload = event.payload or {}
        item_id = payload.get("inventory_item_id")
        msg = action.get(
            "message",
            "Inventory is below threshold.",
        )

        if not item_id:
            return {"status": "skipped", "reason": "missing_inventory_item_id"}

        alert = Alert(
            workspace_id=event.workspace_id,
            severity=AlertSeverity.error,
            source=AlertSource.automation,
            code="inventory.low_stock_escalated",
            message=msg,
            context=payload,
        )
        self.db.add(alert)
        return {"status": "alert_created", "alert_id": str(alert.id)}

    def _act_pause_automation_for_conversation(
        self, action: dict, event: EventLog
    ) -> dict:
        """
        Trigger: event_type = 'message.queued' with ActorType.staff,
        used for 'Staff reply → pause automation'.
        """
        booking_conv_id = None
        # For staff replies we expect entity_type="message" and payload has conversation_id
        payload = event.payload or {}
        conv_id = payload.get("conversation_id")
        if not conv_id:
            return {"status": "skipped", "reason": "missing_conversation_id"}

        conv = self.db.get(Conversation, UUID(conv_id))
        if not conv:
            return {"status": "skipped", "reason": "conversation_not_found"}

        conv.automation_paused = True
        conv.last_staff_reply_at = event.created_at

        # Log explicit automation pause event
        self._log_automation_event(
            conv.workspace_id,
            "automation.paused",
            entity_type="conversation",
            entity_id=str(conv.id),
        )
        return {"status": "paused", "conversation_id": str(conv.id)}

    # ---------- Entity helpers ----------

    def _get_contact_from_event(self, event: EventLog) -> Contact:
        if event.entity_type == "contact":
            return self.db.get(Contact, UUID(event.entity_id))
        payload = event.payload or {}
        contact_id = payload.get("contact_id")
        if not contact_id:
            raise ValueError("contact_id missing in event for automation rule.")
        return self.db.get(Contact, UUID(contact_id))

    def _get_booking_from_event(self, event: EventLog) -> Booking:
        if event.entity_type == "booking":
            return self.db.get(Booking, UUID(event.entity_id))
        payload = event.payload or {}
        booking_id = payload.get("booking_id")
        if not booking_id:
            raise ValueError("booking_id missing in event for automation rule.")
        return self.db.get(Booking, UUID(booking_id))

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
        return conv

    # ---------- Automation event logging ----------

    def _log_automation_event(
        self,
        workspace_id: UUID,
        event_type: str,
        run: AutomationRun | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
    ) -> None:
        payload: dict[str, Any] = {}
        if run:
            payload.update(
                {
                    "run_id": str(run.id),
                    "rule_id": str(run.rule_id),
                    "event_id": str(run.event_id),
                    "status": run.status.value,
                    "error_message": run.error_message,
                }
            )

        ev = EventLog(
            workspace_id=workspace_id,
            event_type=event_type,
            entity_type=entity_type or "automation_run",
            entity_id=entity_id or (str(run.id) if run else None),
            actor_type=ActorType.system,
            payload=payload,
        )
        self.db.add(ev)