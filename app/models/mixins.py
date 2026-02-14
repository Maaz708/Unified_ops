# app/models/mixins.py
import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, declared_attr
from sqlalchemy import func, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID

class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

class WorkspaceScopedMixin:
    @declared_attr
    def workspace_id(cls) -> Mapped[uuid.UUID]:
        from sqlalchemy import ForeignKey
        return mapped_column(
            UUID(as_uuid=True),
            ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        )
class SoftDeleteMixin:
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))