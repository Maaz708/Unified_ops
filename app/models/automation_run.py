# app/models/automation_run.py
from __future__ import annotations

from datetime import datetime
import uuid
from sqlalchemy import String, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

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


class AutomationRunStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    skipped = "skipped"


class AutomationRun(Base, UUIDMixin, TimestampMixin, WorkspaceScopedMixin):
    __tablename__ = "automation_runs"
    __table_args__ = (
        Index(
            "ix_automation_runs_workspace_status",
            "workspace_id",
            "status",
            "created_at",
        ),
    )

    rule_id: Mapped["uuid.UUID"] = mapped_column(
        ForeignKey("automation_rules.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_id: Mapped["uuid.UUID"] = mapped_column(
        ForeignKey("event_log.id", ondelete="CASCADE"),
        nullable=False,
    )

    status: Mapped[AutomationRunStatus] = mapped_column(
        Enum(AutomationRunStatus, name="automation_run_status"),
        nullable=False,
        default=AutomationRunStatus.pending,
    )
    error_message: Mapped[str | None] = mapped_column(String(1024))
    run_metadata: Mapped[dict | None] = mapped_column(JSONB, name="metadata")

    rule: Mapped["AutomationRule"] = relationship("AutomationRule")
    event: Mapped["EventLog"] = relationship("EventLog")