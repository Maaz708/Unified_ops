from __future__ import annotations

# app/models/form_submission.py
from datetime import datetime
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base
from .mixins import UUIDMixin, TimestampMixin, WorkspaceScopedMixin

if TYPE_CHECKING:
    from .workspace import Workspace
    from .form_template import FormTemplate
    from .booking import Booking
    from .contact import Contact


class FormSubmission(Base, UUIDMixin, TimestampMixin, WorkspaceScopedMixin):
    __tablename__ = "form_submissions"
    __table_args__ = (
        Index(
            "ix_form_submissions_workspace_form",
            "workspace_id",
            "form_template_id",
            "created_at",
        ),
    )

    form_template_id: Mapped["uuid.UUID"] = mapped_column(
        ForeignKey("form_templates.id", ondelete="RESTRICT"),
        nullable=False,
    )
    booking_id: Mapped["uuid.UUID"] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
    )
    contact_id: Mapped["uuid.UUID"] = mapped_column(
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
    )

    submitted_at: Mapped[datetime] = mapped_column(nullable=False)
    answers: Mapped[dict] = mapped_column(JSONB, nullable=False)

    workspace: Mapped["Workspace"] = relationship(
        "Workspace", back_populates="form_submissions"
    )
    form_template: Mapped["FormTemplate"] = relationship(
        "FormTemplate", back_populates="submissions"
    )
    booking: Mapped["Booking"] = relationship(
        "Booking", back_populates="form_submissions"
    )
    contact: Mapped["Contact"] = relationship(
        "Contact", back_populates="form_submissions"
    )