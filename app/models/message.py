# app/models/message.py
from __future__ import annotations

from sqlalchemy import Enum, String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum
import uuid

from typing import TYPE_CHECKING

from app.core.database import Base
# existing imports...

if TYPE_CHECKING:
    from .workspace import Workspace
    from .booking import Booking
    from .contact import Contact
    from .conversation import Conversation
    from .form_submission import FormSubmission
    from .inventory_item import InventoryItem
    from .inventory_usage_log import InventoryUsageLog
    from .users import StaffUser
    from .alert import Alert
    from .event_log import EventLog
    from .automation_rule import AutomationRule
    # etc, only those actually referenced in this file


from app.core.database import Base
from .mixins import UUIDMixin, TimestampMixin, WorkspaceScopedMixin


class MessageDirection(str, enum.Enum):
    inbound = "inbound"
    outbound = "outbound"


class MessageChannel(str, enum.Enum):
    email = "email"
    sms = "sms"


class MessageStatus(str, enum.Enum):
    queued = "queued"
    sent = "sent"
    delivered = "delivered"
    failed = "failed"


class Message(Base, UUIDMixin, TimestampMixin, WorkspaceScopedMixin):
    __tablename__ = "messages"
    __table_args__ = (
        Index(
            "ix_messages_workspace_conversation",
            "workspace_id",
            "conversation_id",
            "created_at",
        ),
        Index("ix_messages_workspace_status", "workspace_id", "status", "created_at"),
    )

    conversation_id: Mapped["uuid.UUID"] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    direction: Mapped[MessageDirection] = mapped_column(
        Enum(MessageDirection, name="message_direction"),
        nullable=False,
    )
    channel: Mapped[MessageChannel] = mapped_column(
        Enum(MessageChannel, name="message_channel"),
        nullable=False,
    )
    subject: Mapped[str | None] = mapped_column(String(255))
    body_text: Mapped[str]
    body_html: Mapped[str | None]
    from_address: Mapped[str | None] = mapped_column(String(255))
    to_address: Mapped[str | None] = mapped_column(String(255))
    from_phone: Mapped[str | None] = mapped_column(String(50))
    to_phone: Mapped[str | None] = mapped_column(String(50))
    provider_message_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[MessageStatus] = mapped_column(
        Enum(MessageStatus, name="message_status"),
        default=MessageStatus.queued,
        nullable=False,
    )
    error_code: Mapped[str | None] = mapped_column(String(255))
    infodata: Mapped[dict | None] = mapped_column(JSONB)

    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="messages")
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )