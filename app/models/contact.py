from __future__ import annotations

# app/models/contact.py
from typing import TYPE_CHECKING

from sqlalchemy import String, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base
from .mixins import UUIDMixin, TimestampMixin, WorkspaceScopedMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from .workspace import Workspace
    from .conversation import Conversation
    from .booking import Booking
    from .form_submission import FormSubmission


class Contact(Base, UUIDMixin, TimestampMixin, WorkspaceScopedMixin, SoftDeleteMixin):
    __tablename__ = "contacts"
    __table_args__ = (
        Index("ix_contacts_workspace_email", "workspace_id", "primary_email"),
        Index("ix_contacts_workspace_phone", "workspace_id", "primary_phone"),
    )

    full_name: Mapped[str] = mapped_column(String(255))
    primary_email: Mapped[str | None] = mapped_column(String(255))
    primary_phone: Mapped[str | None] = mapped_column(String(50))
    external_id: Mapped[str | None] = mapped_column(String(255))

    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="contacts")
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="contact", uselist=False
    )
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="contact")
    form_submissions: Mapped[list["FormSubmission"]] = relationship(
        "FormSubmission", back_populates="contact"
    )