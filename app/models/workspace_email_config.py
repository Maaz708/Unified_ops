# app/models/workspace_email_config.py
from __future__ import annotations

from sqlalchemy import String, Boolean, UniqueConstraint, Index, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base
from app.models.mixins import UUIDMixin, TimestampMixin, WorkspaceScopedMixin

from typing import TYPE_CHECKING

from app.core.database import Base
# existing imports...

if TYPE_CHECKING:
    from .workspace import Workspace
    
    # etc, only those actually referenced in this file


class EmailProvider(str, enum.Enum):
    resend = "resend"


class WorkspaceEmailConfig(Base, UUIDMixin, TimestampMixin, WorkspaceScopedMixin):
    __tablename__ = "workspace_email_configs"
    __table_args__ = (
        UniqueConstraint("workspace_id", name="uq_workspace_email_config_per_ws"),
        Index("ix_workspace_email_config_workspace_active", "workspace_id", "is_active"),
    )

    provider: Mapped[EmailProvider] = mapped_column(
        Enum(EmailProvider, name="email_provider"),
        nullable=False,
    )
    from_email: Mapped[str] = mapped_column(String(255), nullable=False)
    from_name: Mapped[str | None] = mapped_column(String(255))
    api_key_alias: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # e.g. "default-resend" (actual key in env/secret store)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="email_config")