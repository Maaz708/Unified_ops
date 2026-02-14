# app/services/communication_service.py
from __future__ import annotations

from typing import Optional
from uuid import UUID

from loguru import logger
from sqlalchemy.orm import Session

from app.models.message import Message, MessageStatus, MessageChannel
from app.models.workspace_email_config import WorkspaceEmailConfig
from app.models.alert import Alert, AlertSeverity, AlertSource
from app.models.event_log import EventLog, ActorType
from app.services.email_service import EmailService
from app.core.config import settings



class CommunicationService:
    """
    Abstraction over email/SMS providers.

    Responsibilities:
    - Look up workspace-level channel config
    - Dispatch email/SMS via integration modules
    - Update Message status / provider IDs
    - Log events and create alerts on failure
    """

    def __init__(self, db: Session):
        self.db = db

    def send_outbound_message(self, message: Message) -> None:
        if message.channel == MessageChannel.email:
            self._send_email(message)
        elif message.channel == MessageChannel.sms:
            self._send_sms(message)

    # ----- Internal -----

    def _send_email(self, message: Message) -> None:
        from sqlalchemy import select

        cfg = self.db.scalar(
            select(WorkspaceEmailConfig).where(
                WorkspaceEmailConfig.workspace_id == message.workspace_id,
                WorkspaceEmailConfig.is_active.is_(True),
            )
        )
        if cfg:
            from_email = (
                f"{cfg.from_name} <{cfg.from_email}>" if cfg.from_name else cfg.from_email
            )
        else:
            # Fallback: use app-level Resend so inbox replies still send without workspace email config
            if not getattr(settings, "resend_api_key", None):
                logger.warning("Inbox reply: no workspace email config and no RESEND_API_KEY in backend .env")
                self._mark_failed(
                    message,
                    reason="EMAIL_PROVIDER_NOT_CONFIGURED",
                    details="No workspace email config and no RESEND_API_KEY.",
                )
                return
            from_email = getattr(settings, "resend_from_email", None) or "onboarding@resend.dev"
            logger.info("Inbox reply: using app-level Resend fallback, from={}", from_email)

        email_service = EmailService()
        to_address = message.to_address or ""
        if not to_address:
            logger.warning("Inbox reply: message has no to_address (message_id={})", message.id)
            self._mark_failed(message, reason="NO_RECIPIENT", details="Message has no to_address.")
            return

        logger.info(
            "Inbox reply: sending email to={} from={} subject={}",
            to_address,
            from_email,
            (message.subject or "(No subject)")[:50],
        )
        result = email_service.send_email(
            from_email=from_email,
            to=to_address,
            subject=message.subject or "(No subject)",
            text=message.body_text,
            html=message.body_html,
            tags={"workspace_id": str(message.workspace_id)},
        )

        if not result["ok"]:
            logger.error(
                "Inbox reply: Resend failed to={} error={} status={}",
                to_address,
                result.get("error"),
                result.get("status_code"),
            )
            self._mark_failed(
                message,
                reason=result.get("error") or "EMAIL_SEND_FAILED",
                details=f"Resend failure (status={result.get('status_code')})",
            )
            return

        logger.info("Inbox reply: sent successfully to={} message_id={}", to_address, result.get("message_id"))
        message.status = MessageStatus.sent
        message.provider_message_id = result.get("message_id")
        self._log_event(
            workspace_id=message.workspace_id,
            event_type="message.sent",
            entity_type="message",
            entity_id=str(message.id),
            payload={"channel": "email", "provider_message_id": message.provider_message_id},
        )

    def _send_sms(self, message: Message) -> None:
        # TODO: integrate with SMS provider
        message.status = MessageStatus.sent

        self._log_event(
            workspace_id=message.workspace_id,
            event_type="message.sent",
            entity_type="message",
            entity_id=str(message.id),
            payload={"channel": "sms"},
        )

    def _mark_failed(self, message: Message, reason: str, details: str) -> None:
        message.status = MessageStatus.failed
        message.error_code = reason

        self._log_event(
            workspace_id=message.workspace_id,
            event_type="message.failed",
            entity_type="message",
            entity_id=str(message.id),
            payload={"reason": reason, "details": details},
        )

        alert = Alert(
            workspace_id=message.workspace_id,
            severity=AlertSeverity.error,
            source=AlertSource.integration,
            code=reason,
            message=f"Failed to send {message.channel.value} message",
            context={"message_id": str(message.id), "details": details},
        )
        self.db.add(alert)

    def _log_event(
        self,
        workspace_id: UUID,
        event_type: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        payload: Optional[dict] = None,
    ) -> None:
        ev = EventLog(
            workspace_id=workspace_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_type=ActorType.system,
            payload=payload or {},
        )
        self.db.add(ev)