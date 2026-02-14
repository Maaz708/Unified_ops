# app/models/alert.py
from __future__ import annotations

from datetime import datetime
import enum
import uuid

from sqlalchemy import String, Enum, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base
from .mixins import UUIDMixin, TimestampMixin, WorkspaceScopedMixin

from typing import TYPE_CHECKING

from app.core.database import Base
# existing imports...

if TYPE_CHECKING:
    from .workspace import Workspace
    from .booking import Booking
    from .contact import Contact
    from .conversation import Conversation
    from .form_submission import FormSubmission
    from .inventory_item import InventoryItem
    from .inventory_usage_log import InventoryUsageLog
    from .users import StaffUser
    from .alert import Alert
    from .event_log import EventLog
    from .automation_rule import AutomationRule
    # etc, only those actually referenced in this file



class AlertSeverity(str, enum.Enum):
    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


class AlertSource(str, enum.Enum):
    system = "system"
    integration = "integration"
    automation = "automation"
    ai = "ai"


class Alert(Base, UUIDMixin, TimestampMixin, WorkspaceScopedMixin):
    __tablename__ = "alerts"
    __table_args__ = (
        Index(
            "ix_alerts_workspace_severity",
            "workspace_id",
            "severity",
            "created_at",
        ),
        Index(
            "ix_alerts_workspace_ack",
            "workspace_id",
            "acknowledged",
            "created_at",
        ),
    )

    severity: Mapped[AlertSeverity] = mapped_column(
        Enum(AlertSeverity, name="alert_severity"),
        nullable=False,
    )
    source: Mapped[AlertSource] = mapped_column(
        Enum(AlertSource, name="alert_source"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(String(1024), nullable=False)
    context: Mapped[dict | None] = mapped_column(JSONB)

    acknowledged: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    acknowledged_by_id: Mapped["uuid.UUID | None"] = mapped_column(
        ForeignKey("staff_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    acknowledged_at: Mapped[datetime | None]

    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="alerts")
    acknowledged_by: Mapped["StaffUser | None"] = relationship(
        "StaffUser", back_populates="acknowledged_alerts"
    )