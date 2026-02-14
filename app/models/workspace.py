from __future__ import annotations

# app/models/workspace.py
import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, Enum, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base
from .mixins import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from .workspace_email_config import WorkspaceEmailConfig
    from .users import StaffUser
    from .contact import Contact
    from .conversation import Conversation
    from .message import Message
    from .booking_type import BookingType
    from .booking import Booking
    from .availability_slot import AvailabilitySlot
    from .form_template import FormTemplate
    from .form_submission import FormSubmission
    from .inventory_item import InventoryItem
    from .inventory_usage_log import InventoryUsageLog
    from .alert import Alert
    from .event_log import EventLog
    from .automation_rule import AutomationRule


class WorkspaceStatus(str, enum.Enum):
    draft = "draft"
    pending_validation = "pending_validation"
    active = "active"
    suspended = "suspended"


class Workspace(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workspaces"
    __table_args__ = (
        Index("ix_workspaces_status", "status"),
        Index("ix_workspaces_created_at", "created_at"),
    )
    # app/models/workspace.py (inside class Workspace)
    email_config: Mapped["WorkspaceEmailConfig | None"] = relationship(
        "WorkspaceEmailConfig",
        back_populates="workspace",
        uselist=False,
        cascade="all, delete-orphan",
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[WorkspaceStatus] = mapped_column(
        Enum(WorkspaceStatus, name="workspace_status"),
        default=WorkspaceStatus.draft,
        nullable=False,
    )
    owner_id: Mapped["uuid.UUID | None"] = mapped_column(nullable=True)

    staff_users: Mapped[list["StaffUser"]] = relationship(
        "StaffUser", back_populates="workspace", cascade="all, delete-orphan"
    )
    contacts: Mapped[list["Contact"]] = relationship(
        "Contact", back_populates="workspace", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="workspace", cascade="all, delete-orphan"
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="workspace", cascade="all, delete-orphan"
    )
    booking_types: Mapped[list["BookingType"]] = relationship(
        "BookingType", back_populates="workspace", cascade="all, delete-orphan"
    )
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking", back_populates="workspace", cascade="all, delete-orphan"
    )
    availability_slots: Mapped[list["AvailabilitySlot"]] = relationship(
        "AvailabilitySlot", back_populates="workspace", cascade="all, delete-orphan"
    )
    form_templates: Mapped[list["FormTemplate"]] = relationship(
        "FormTemplate", back_populates="workspace", cascade="all, delete-orphan"
    )
    form_submissions: Mapped[list["FormSubmission"]] = relationship(
        "FormSubmission", back_populates="workspace", cascade="all, delete-orphan"
    )
    inventory_items: Mapped[list["InventoryItem"]] = relationship(
        "InventoryItem", back_populates="workspace", cascade="all, delete-orphan"
    )
    inventory_usage_logs: Mapped[list["InventoryUsageLog"]] = relationship(
        "InventoryUsageLog", back_populates="workspace", cascade="all, delete-orphan"
    )
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert", back_populates="workspace", cascade="all, delete-orphan"
    )
    events: Mapped[list["EventLog"]] = relationship(
        "EventLog", back_populates="workspace", cascade="all, delete-orphan"
    )
    automation_rules: Mapped[list["AutomationRule"]] = relationship(
        "AutomationRule", back_populates="workspace", cascade="all, delete-orphan"
    )