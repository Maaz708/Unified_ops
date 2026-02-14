from __future__ import annotations

# app/models/form_template.py
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, UniqueConstraint, Index, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base
from .mixins import UUIDMixin, TimestampMixin, WorkspaceScopedMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from .workspace import Workspace
    from .form_submission import FormSubmission
    from .booking_type import BookingType


class FormTemplate(
    Base,
    UUIDMixin,
    TimestampMixin,
    WorkspaceScopedMixin,
    SoftDeleteMixin,
):
    __tablename__ = "form_templates"
    __table_args__ = (
        UniqueConstraint("workspace_id", "name", name="uq_form_template_name_ws"),
        Index(
            "ix_form_templates_workspace_active",
            "workspace_id",
            "is_deleted",
        ),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    schema: Mapped[dict] = mapped_column(JSONB, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    stay_active_after_submission: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    booking_type_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("booking_types.id", ondelete="SET NULL"),
        nullable=True,
    )

    workspace: Mapped["Workspace"] = relationship(
        "Workspace", back_populates="form_templates"
    )
    booking_type: Mapped["BookingType | None"] = relationship(
        "BookingType", back_populates="form_templates", foreign_keys=[booking_type_id]
    )
    submissions: Mapped[list["FormSubmission"]] = relationship(
        "FormSubmission", back_populates="form_template"
    )