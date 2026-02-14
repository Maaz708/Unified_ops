# app/models/event_log.py
from __future__ import annotations

from sqlalchemy import String, Enum, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

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


from app.core.database import Base
from .mixins import UUIDMixin, TimestampMixin, WorkspaceScopedMixin


class ActorType(str, enum.Enum):
    system = "system"
    staff = "staff"
    contact = "contact"
    integration = "integration"


class EventLog(Base, UUIDMixin, TimestampMixin, WorkspaceScopedMixin):
    __tablename__ = "event_log"
    __table_args__ = (
        Index("ix_events_workspace_created", "workspace_id", "created_at"),
        Index(
            "ix_events_workspace_type_created",
            "workspace_id",
            "event_type",
            "created_at",
        ),
        Index(
            "ix_events_entity",
            "workspace_id",
            "entity_type",
            "entity_id",
            "created_at",
        ),
    )

    event_type: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50))
    entity_id: Mapped[str | None] = mapped_column(String(255))

    actor_type: Mapped[ActorType] = mapped_column(
        Enum(ActorType, name="event_actor_type"),
        nullable=False,
    )
    actor_id: Mapped[str | None] = mapped_column(String(255))
    correlation_id: Mapped[str | None] = mapped_column(String(255))

    payload: Mapped[dict | None] = mapped_column(JSONB)

    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="events")