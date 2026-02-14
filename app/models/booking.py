from __future__ import annotations

# app/models/booking.py
from datetime import datetime
import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import TSTZRANGE, JSONB
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base
from .mixins import UUIDMixin, TimestampMixin, WorkspaceScopedMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from .workspace import Workspace
    from .contact import Contact
    from .booking_type import BookingType
    from .users import StaffUser
    from .conversation import Conversation
    from .form_submission import FormSubmission
    from .inventory_usage_log import InventoryUsageLog


class BookingStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"
    no_show = "no_show"


class BookingSource(str, enum.Enum):
    public_page = "public_page"
    internal = "internal"
    import_ = "import"


class Booking(Base, UUIDMixin, TimestampMixin, WorkspaceScopedMixin, SoftDeleteMixin):
    __tablename__ = "bookings"
    __table_args__ = (
        # Prevent double booking per staff per time range in a workspace
        ExcludeConstraint(
            ("workspace_id", "="),
            ("assigned_staff_id", "="),
            ("time_range", "&&"),
            name="excl_booking_per_staff_time",
            using="gist",
        ),
        Index(
            "ix_bookings_workspace_contact",
            "workspace_id",
            "contact_id",
            "start_at",
        ),
        Index(
            "ix_bookings_workspace_status",
            "workspace_id",
            "status",
            "start_at",
        ),
    )

    contact_id: Mapped["uuid.UUID"] = mapped_column(
        ForeignKey("contacts.id", ondelete="RESTRICT"),
        nullable=False,
    )
    booking_type_id: Mapped["uuid.UUID"] = mapped_column(
        ForeignKey("booking_types.id", ondelete="RESTRICT"),
        nullable=False,
    )
    assigned_staff_id: Mapped["uuid.UUID | None"] = mapped_column(
        ForeignKey("staff_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    conversation_id: Mapped["uuid.UUID | None"] = mapped_column(
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
    )

    start_at: Mapped[datetime] = mapped_column(nullable=False)
    end_at: Mapped[datetime] = mapped_column(nullable=False)
    # For exclusion constraint: tstzrange(start_at, end_at)
    time_range: Mapped[tuple[datetime, datetime]] = mapped_column(
        TSTZRANGE, nullable=False
    )

    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name="booking_status"),
        default=BookingStatus.pending,
        nullable=False,
    )
    source: Mapped[BookingSource] = mapped_column(
        Enum(BookingSource, name="booking_source"),
        default=BookingSource.public_page,
        nullable=False,
    )
    location: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None]
    infodata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="bookings")
    contact: Mapped["Contact"] = relationship("Contact", back_populates="bookings")
    booking_type: Mapped["BookingType"] = relationship(
        "BookingType", back_populates="bookings"
    )
    assigned_staff: Mapped["StaffUser | None"] = relationship(
        "StaffUser", back_populates="bookings", foreign_keys=[assigned_staff_id]
    )
    conversation: Mapped["Conversation | None"] = relationship("Conversation")
    form_submissions: Mapped[list["FormSubmission"]] = relationship(
        "FormSubmission", back_populates="booking"
    )
    inventory_usage_logs: Mapped[list["InventoryUsageLog"]] = relationship(
        "InventoryUsageLog", back_populates="booking"
    )