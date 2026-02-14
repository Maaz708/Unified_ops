# app/models/availability_slot.py
from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base
from .mixins import UUIDMixin, TimestampMixin, WorkspaceScopedMixin


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .booking_type import BookingType
    from .users import StaffUser
    from .workspace import Workspace


class AvailabilitySlot(Base, UUIDMixin, TimestampMixin, WorkspaceScopedMixin):
    __tablename__ = "availability_slots"
    __table_args__ = (
        Index(
            "ix_availability_workspace_staff_start",
            "workspace_id",
            "staff_user_id",
            "start_at",
        ),
    )

    booking_type_id: Mapped["uuid.UUID"] = mapped_column(
        ForeignKey("booking_types.id", ondelete="CASCADE"),
        nullable=False,
    )
    staff_user_id: Mapped["uuid.UUID | None"] = mapped_column(
        ForeignKey("staff_users.id", ondelete="CASCADE"),
        nullable=True,
    )

    start_at: Mapped[datetime] = mapped_column(nullable=False)
    end_at: Mapped[datetime] = mapped_column(nullable=False)

    workspace: Mapped["Workspace"] = relationship(
        "Workspace", back_populates="availability_slots"
    )
    booking_type: Mapped["BookingType"] = relationship(
        "BookingType", back_populates="availability_slots"
    )
    staff_user: Mapped["StaffUser | None"] = relationship(
        "StaffUser", back_populates="availability_slots"
    )