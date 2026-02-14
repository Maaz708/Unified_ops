from __future__ import annotations

# app/models/users.py
import enum
from typing import TYPE_CHECKING

from sqlalchemy import String, Enum, Boolean, UniqueConstraint, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base
from .mixins import UUIDMixin, TimestampMixin, WorkspaceScopedMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from .workspace import Workspace
    from .booking import Booking
    from .availability_slot import AvailabilitySlot
    from .alert import Alert


class StaffRole(str, enum.Enum):
    owner = "owner"
    staff = "staff"


class StaffUser(Base, UUIDMixin, TimestampMixin, WorkspaceScopedMixin, SoftDeleteMixin):
    __tablename__ = "staff_users"
    __table_args__ = (
        UniqueConstraint("workspace_id", "email", name="uq_staff_email_per_workspace"),
        Index("ix_staff_workspace_active", "workspace_id", "is_active"),
    )

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[StaffRole] = mapped_column(
        Enum(StaffRole, name="staff_role"),
        default=StaffRole.staff,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="staff_users")
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking",
        back_populates="assigned_staff",
        foreign_keys="Booking.assigned_staff_id",
    )
    availability_slots: Mapped[list["AvailabilitySlot"]] = relationship(
        "AvailabilitySlot", back_populates="staff_user"
    )
    acknowledged_alerts: Mapped[list["Alert"]] = relationship(
        "Alert",
        back_populates="acknowledged_by",
        foreign_keys="Alert.acknowledged_by_id",
    )