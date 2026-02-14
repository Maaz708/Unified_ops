from __future__ import annotations

# app/models/conversation.py
from datetime import datetime
import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, UniqueConstraint, Index, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base
from .mixins import UUIDMixin, TimestampMixin, WorkspaceScopedMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from .workspace import Workspace
    from .contact import Contact
    from .message import Message


class ConversationStatus(str, enum.Enum):
    open = "open"
    closed = "closed"
    snoozed = "snoozed"


class ChannelPreference(str, enum.Enum):
    email = "email"
    sms = "sms"
    mixed = "mixed"


class Conversation(
    Base,
    UUIDMixin,
    TimestampMixin,
    WorkspaceScopedMixin,
    SoftDeleteMixin,
):
    __tablename__ = "conversations"
    __table_args__ = (
        UniqueConstraint("contact_id", name="uq_conversations_contact_id"),
        Index(
            "ix_conversations_workspace_status",
            "workspace_id",
            "status",
            "updated_at",
        ),
    )

    contact_id: Mapped["uuid.UUID"] = mapped_column(
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus, name="conversation_status"),
        default=ConversationStatus.open,
        nullable=False,
    )
    channel_preference: Mapped[ChannelPreference] = mapped_column(
        Enum(ChannelPreference, name="channel_preference"),
        default=ChannelPreference.mixed,
        nullable=False,
    )
    last_message_at: Mapped[datetime | None]
     # NEW: automation pause state
    automation_paused: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    last_staff_reply_at: Mapped[datetime | None]

    # relationships unchanged...

    workspace: Mapped["Workspace"] = relationship(
        "Workspace", back_populates="conversations"
    )
    contact: Mapped["Contact"] = relationship("Contact", back_populates="conversation")
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )