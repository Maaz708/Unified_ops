# app/schemas/message.py
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models.message import MessageChannel, MessageDirection, MessageStatus


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class StaffSendMessageRequest(BaseModel):
    contact_id: str
    channel: MessageChannel
    subject: Optional[str] = None  # email only
    body: str = Field(..., min_length=1)
    to_email: Optional[EmailStr] = None  # for email
    to_phone: Optional[str] = Field(default=None, max_length=50)

    def validate_channel_payload(self) -> None:
        if self.channel == MessageChannel.email:
            if not self.to_email:
                raise ValueError("to_email is required for email messages")
        if self.channel == MessageChannel.sms:
            if not self.to_phone:
                raise ValueError("to_phone is required for SMS messages")


class InboundMessageWebhook(BaseModel):
    workspace_id: str
    channel: MessageChannel
    conversation_external_id: Optional[str] = None  # if provider passes it
    from_email: Optional[EmailStr] = None
    from_phone: Optional[str] = None
    to_email: Optional[EmailStr] = None
    to_phone: Optional[str] = None
    subject: Optional[str] = None
    body: str

    # Provider timestamps are often local; normalise upstream if possible
    received_at: Optional[datetime] = None

    def normalized_received_at(self) -> datetime:
        return _ensure_utc(self.received_at or datetime.now(timezone.utc))


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    direction: MessageDirection
    channel: MessageChannel
    subject: Optional[str]
    body_text: str
    status: MessageStatus
    created_at: datetime