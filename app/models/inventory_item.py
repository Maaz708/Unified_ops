from __future__ import annotations

# app/models/inventory_item.py
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base
from .mixins import UUIDMixin, TimestampMixin, WorkspaceScopedMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from .workspace import Workspace
    from .inventory_usage_log import InventoryUsageLog


class InventoryItem(
    Base,
    UUIDMixin,
    TimestampMixin,
    WorkspaceScopedMixin,
    SoftDeleteMixin,
):
    __tablename__ = "inventory_items"
    __table_args__ = (
        UniqueConstraint("workspace_id", "sku", name="uq_inventory_sku_ws"),
        Index(
            "ix_inventory_items_workspace_active",
            "workspace_id",
            "is_deleted",
        ),
    )

    sku: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None]
    current_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reorder_threshold: Mapped[int | None] = mapped_column(Integer)
    unit: Mapped[str | None] = mapped_column(String(50))
    infodata: Mapped[dict | None] = mapped_column(JSONB)

    workspace: Mapped["Workspace"] = relationship(
        "Workspace", back_populates="inventory_items"
    )
    usage_logs: Mapped[list["InventoryUsageLog"]] = relationship(
        "InventoryUsageLog", back_populates="item"
    )