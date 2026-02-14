# app/models/booking_type.py
from __future__ import annotations

from sqlalchemy import String, Boolean, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base
from .mixins import UUIDMixin, TimestampMixin, WorkspaceScopedMixin, SoftDeleteMixin


from typing import TYPE_CHECKING

from app.core.database import Base
# existing imports...

if TYPE_CHECKING:
    from .workspace import Workspace
    from .booking import Booking
    from .contact import Contact
    from .conversation import Conversation
    from .form_submission import FormSubmission
    from .form_template import FormTemplate
    from .inventory_item import InventoryItem
    from .inventory_usage_log import InventoryUsageLog
    from .users import StaffUser
    from .alert import Alert
    from .event_log import EventLog
    from .automation_rule import AutomationRule
    # etc, only those actually referenced in this file


class BookingType(Base, UUIDMixin, TimestampMixin, WorkspaceScopedMixin, SoftDeleteMixin):
    __tablename__ = "booking_types"
    __table_args__ = (
        UniqueConstraint("workspace_id", "slug", name="uq_booking_type_slug_per_ws"),
        Index("ix_booking_types_workspace_active", "workspace_id", "is_deleted"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None]
    duration_minutes: Mapped[int]
    infodata: Mapped[dict | None] = mapped_column(JSONB)

    workspace: Mapped["Workspace"] = relationship(
        "Workspace", back_populates="booking_types"
    )
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking", back_populates="booking_type"
    )
    availability_slots: Mapped[list["AvailabilitySlot"]] = relationship(
        "AvailabilitySlot", back_populates="booking_type"
    )
    form_templates: Mapped[list["FormTemplate"]] = relationship(
        "FormTemplate", back_populates="booking_type"
    )