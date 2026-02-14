# app/models/automation_rule.py
from __future__ import annotations

from sqlalchemy import String, Boolean, Integer, Index
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
    from .inventory_item import InventoryItem
    from .inventory_usage_log import InventoryUsageLog
    from .users import StaffUser
    from .alert import Alert
    from .event_log import EventLog
    from .automation_rule import AutomationRule
    # etc, only those actually referenced in this file


class AutomationRule(
    Base,
    UUIDMixin,
    TimestampMixin,
    WorkspaceScopedMixin,
    SoftDeleteMixin,
):
    __tablename__ = "automation_rules"
    __table_args__ = (
        Index(
            "ix_automation_rules_workspace_event_active",
            "workspace_id",
            "event_type",
            "is_deleted",
            "is_active",
        ),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None]
    event_type: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    conditions: Mapped[dict | None] = mapped_column(JSONB)  # filter spec
    actions: Mapped[dict] = mapped_column(JSONB, nullable=False)  # list of actions

    workspace: Mapped["Workspace"] = relationship(
        "Workspace", back_populates="automation_rules"
    )