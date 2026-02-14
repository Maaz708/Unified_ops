# app/services/analytics_service.py
from __future__ import annotations

from datetime import datetime, date, timedelta, timezone
from typing import List, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session

from app.models.booking import Booking, BookingStatus
from app.models.contact import Contact
from app.models.booking_type import BookingType
from app.models.form_submission import FormSubmission
from app.models.inventory_item import InventoryItem
from app.models.alert import Alert, AlertSeverity
from app.models.message import Message, MessageDirection
from app.models.conversation import Conversation, ConversationStatus
from app.schemas.analytics import (
    BookingCard,
    BookingStats,
    FormStats,
    InventoryLowStockItem,
    AlertSummary,
    DashboardOverview,
    AiOperationalSummary,
)
from app.services.ai_service import AIService


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DashboardAnalyticsService:
    """
    Aggregated analytics for the workspace dashboard.

    - Optimized read-only queries
    - Workspace-scoped
    """

    def __init__(self, db: Session):
        self.db = db

    # ---------- Public API ----------

    def get_overview(
        self,
        workspace_id: UUID,
        *,
        unanswered_min_age_minutes: int = 30,
        upcoming_days: int = 7,
        forms_overdue_hours: int = 24,
    ) -> DashboardOverview:
        today_start, today_end = self._today_bounds()
        now = _utc_now()
        upcoming_end = now + timedelta(days=upcoming_days)
        overdue_cutoff = now - timedelta(hours=forms_overdue_hours)

        today_bookings, upcoming_bookings = self._get_today_and_upcoming_bookings(
            workspace_id, today_start, today_end, now, upcoming_end
        )
        recent_booking_history = self._get_recent_booking_history(workspace_id)
        booking_stats = self._get_booking_stats(
            workspace_id, today_start, today_end
        )
        form_stats = self._get_form_stats(
            workspace_id, overdue_cutoff
        )
        low_stock_items = self._get_low_stock_items(workspace_id)
        unanswered_conversations = self._get_unanswered_conversations_count(
            workspace_id, unanswered_min_age_minutes
        )
        active_alerts = self._get_active_alerts(workspace_id)

        return DashboardOverview(
            today_bookings=today_bookings,
            upcoming_bookings=upcoming_bookings,
            recent_booking_history=recent_booking_history,
            booking_stats=booking_stats,
            form_stats=form_stats,
            low_stock_items=low_stock_items,
            unanswered_conversations=unanswered_conversations,
            active_alerts=active_alerts,
        )

    async def get_ai_operational_summary(
        self,
        workspace_id: UUID,
        *,
        unanswered_min_age_minutes: int = 30,
        upcoming_days: int = 7,
        forms_overdue_hours: int = 24,
    ) -> AiOperationalSummary:
        """
        Computes base metrics and calls AIService.analyze_operational_risk().
        Fails safely; always returns a structured response.
        """

        today_start, today_end = self._today_bounds()
        now = _utc_now()
        upcoming_end = now + timedelta(days=upcoming_days)
        overdue_cutoff = now - timedelta(hours=forms_overdue_hours)

        # ---------------------------------------------------
        # Booking stats (no-show rate + trends)
        # ---------------------------------------------------
        completed, no_show = self._get_completed_vs_no_show_counts(workspace_id)
        total_completed_period = completed + no_show
        no_show_rate = (
            float(no_show) / float(total_completed_period)
            if total_completed_period > 0
            else 0.0
        )

        # ---------------------------------------------------
        # Operational metrics
        # ---------------------------------------------------
        unanswered = self._get_unanswered_conversations_count(
            workspace_id, unanswered_min_age_minutes
        )
        form_stats = self._get_form_stats(workspace_id, overdue_cutoff)

        low_stock_items = self._get_low_stock_items(workspace_id)

        today_bookings_count, upcoming_bookings_count = self._get_booking_trend_counts(
            workspace_id,
            today_start,
            today_end,
            now,
            upcoming_end,
        )

        booking_trends = {
            "today": today_bookings_count,
            "upcoming": upcoming_bookings_count,
            "completed": completed,
            "no_show": no_show,
        }

        # ---------------------------------------------------
        # EARLY EXIT — Not enough data for AI
        # ---------------------------------------------------
        if (
            unanswered == 0
            and completed == 0
            and no_show == 0
            and today_bookings_count == 0
            and upcoming_bookings_count == 0
            and not low_stock_items
        ):
            return AiOperationalSummary(
                ok=True,
                overall_risk_level="low",
                summary="Not enough operational data yet to generate AI insights.",
                risks=[],
                recommendations=[],
            )

        # ---------------------------------------------------
        # Thresholds (can be workspace-configurable later)
        # ---------------------------------------------------
        unanswered_threshold = 10
        no_show_threshold = 0.10  # 10%
        pending_forms_threshold = 20

        # ---------------------------------------------------
        # AI Analysis (FAIL-SAFE)
        # ---------------------------------------------------
        ai = AIService()

        try:
            raw = await ai.analyze_operational_risk(
                unanswered_count=unanswered,
                unanswered_threshold=unanswered_threshold,
                no_show_rate=no_show_rate,
                no_show_threshold=no_show_threshold,
                pending_forms=form_stats.pending,
                pending_forms_threshold=pending_forms_threshold,
                low_stock_items=[
                    {
                        "id": str(item.id),
                        "sku": item.sku,
                        "name": item.name,
                        "current_quantity": item.current_quantity,
                        "reorder_threshold": item.reorder_threshold,
                        "unit": item.unit,
                    }
                    for item in low_stock_items
                ],
                booking_trends=booking_trends,
            )
        except Exception:
            return AiOperationalSummary(
                ok=False,
                overall_risk_level="unknown",
                summary="AI operational analysis is temporarily unavailable.",
                risks=[],
                recommendations=[],
            )

        # ---------------------------------------------------
        # Normalize AI response
        # ---------------------------------------------------
        return AiOperationalSummary(
            ok=bool(raw.get("ok", True)),
            overall_risk_level=str(raw.get("overall_risk_level", "unknown")),
            summary=str(raw.get("summary", "")),
            risks=raw.get("risks", []),
            recommendations=raw.get("recommendations", []),
        )


    # ---------- Internal helpers ----------

    def _today_bounds(self) -> tuple[datetime, datetime]:
        now = _utc_now()
        today_date = date.fromtimestamp(now.timestamp())
        start = datetime.combine(today_date, datetime.min.time(), tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        return start, end

    # --- Bookings ---

    def _get_today_and_upcoming_bookings(
        self,
        workspace_id: UUID,
        today_start: datetime,
        today_end: datetime,
        now: datetime,
        upcoming_end: datetime,
        limit_per_list: int = 20,
    ) -> tuple[list[BookingCard], list[BookingCard]]:
        # Today
        today_stmt = (
            select(Booking, Contact, BookingType)
            .join(Contact, Booking.contact_id == Contact.id)
            .join(BookingType, Booking.booking_type_id == BookingType.id)
            .where(
                Booking.workspace_id == workspace_id,
                Booking.start_at >= today_start,
                Booking.start_at < today_end,
            )
            .order_by(Booking.start_at.asc())
            .limit(limit_per_list)
        )
        today_rows = self.db.execute(today_stmt).all()
        today_bookings = [
            BookingCard(
                id=b.id,
                start_at=b.start_at,
                end_at=b.end_at,
                status=b.status,
                contact_name=c.full_name,
                booking_type_name=bt.name,
                contact_id=c.id,
                primary_email=c.primary_email,
                primary_phone=c.primary_phone,
            )
            for b, c, bt in today_rows
        ]

        # Upcoming (after now)
        upcoming_stmt = (
            select(Booking, Contact, BookingType)
            .join(Contact, Booking.contact_id == Contact.id)
            .join(BookingType, Booking.booking_type_id == BookingType.id)
            .where(
                Booking.workspace_id == workspace_id,
                Booking.start_at >= now,
                Booking.start_at < upcoming_end,
                Booking.status.in_(
                    [BookingStatus.confirmed, BookingStatus.pending]
                ),
            )
            .order_by(Booking.start_at.asc())
            .limit(limit_per_list)
        )
        upcoming_rows = self.db.execute(upcoming_stmt).all()
        upcoming_bookings = [
            BookingCard(
                id=b.id,
                start_at=b.start_at,
                end_at=b.end_at,
                status=b.status,
                contact_name=c.full_name,
                booking_type_name=bt.name,
                contact_id=c.id,
                primary_email=c.primary_email,
                primary_phone=c.primary_phone,
            )
            for b, c, bt in upcoming_rows
        ]

        return today_bookings, upcoming_bookings

    def _get_recent_booking_history(
        self,
        workspace_id: UUID,
        *,
        limit: int = 30,
        history_days: int = 30,
    ) -> list[BookingCard]:
        """Past/completed bookings for dashboard history (owner & staff)."""
        now = _utc_now()
        history_start = now - timedelta(days=history_days)
        stmt = (
            select(Booking, Contact, BookingType)
            .join(Contact, Booking.contact_id == Contact.id)
            .join(BookingType, Booking.booking_type_id == BookingType.id)
            .where(
                Booking.workspace_id == workspace_id,
                Booking.start_at >= history_start,
                Booking.status.in_(
                    [BookingStatus.completed, BookingStatus.no_show, BookingStatus.cancelled]
                ),
            )
            .order_by(Booking.start_at.desc())
            .limit(limit)
        )
        rows = self.db.execute(stmt).all()
        return [
            BookingCard(
                id=b.id,
                start_at=b.start_at,
                end_at=b.end_at,
                status=b.status,
                contact_name=c.full_name,
                booking_type_name=bt.name,
                contact_id=c.id,
                primary_email=c.primary_email,
                primary_phone=c.primary_phone,
            )
            for b, c, bt in rows
        ]

    def _get_booking_trend_counts(
        self,
        workspace_id: UUID,
        today_start: datetime,
        today_end: datetime,
        now: datetime,
        upcoming_end: datetime,
    ) -> tuple[int, int]:
        today_count = self.db.scalar(
            select(func.count())
            .select_from(Booking)
            .where(
                Booking.workspace_id == workspace_id,
                Booking.start_at >= today_start,
                Booking.start_at < today_end,
            )
        ) or 0

        upcoming_count = self.db.scalar(
            select(func.count())
            .select_from(Booking)
            .where(
                Booking.workspace_id == workspace_id,
                Booking.start_at >= now,
                Booking.start_at < upcoming_end,
                Booking.status.in_(
                    [BookingStatus.confirmed, BookingStatus.pending]
                ),
            )
        ) or 0

        return today_count, upcoming_count

    def _get_booking_stats(
        self,
        workspace_id: UUID,
        today_start: datetime,
        today_end: datetime,
    ) -> BookingStats:
        # Today counts already computed separately; here we focus on completed vs no-show overall
        completed, no_show = self._get_completed_vs_no_show_counts(workspace_id)

        today_count = self.db.scalar(
            select(func.count())
            .select_from(Booking)
            .where(
                Booking.workspace_id == workspace_id,
                Booking.start_at >= today_start,
                Booking.start_at < today_end,
            )
        ) or 0

        upcoming_count = self.db.scalar(
            select(func.count())
            .select_from(Booking)
            .where(
                Booking.workspace_id == workspace_id,
                Booking.start_at >= today_end,
                Booking.status.in_(
                    [BookingStatus.confirmed, BookingStatus.pending]
                ),
            )
        ) or 0

        return BookingStats(
            total_today=today_count,
            total_upcoming=upcoming_count,
            completed=completed,
            no_show=no_show,
        )

    def _get_completed_vs_no_show_counts(
        self,
        workspace_id: UUID,
    ) -> tuple[int, int]:
        stmt = (
            select(
                func.count().filter(Booking.status == BookingStatus.completed),
                func.count().filter(Booking.status == BookingStatus.no_show),
            )
            .select_from(Booking)
            .where(Booking.workspace_id == workspace_id)
        )
        completed, no_show = self.db.execute(stmt).one()
        return int(completed or 0), int(no_show or 0)

    # --- Forms ---

    def _get_form_stats(
        self,
        workspace_id: UUID,
        overdue_cutoff: datetime,
    ) -> FormStats:
        """
        Pending = completed bookings with no submission.
        Overdue = same, but booking start_at older than overdue_cutoff.
        """
        fs_alias = FormSubmission  # simple alias

        base_where = and_(
            Booking.workspace_id == workspace_id,
            Booking.status == BookingStatus.completed,
        )

        # Pending (no submission)
        pending_stmt = (
            select(func.count())
            .select_from(Booking)
            .outerjoin(
                fs_alias,
                and_(
                    fs_alias.workspace_id == Booking.workspace_id,
                    fs_alias.booking_id == Booking.id,
                ),
            )
            .where(
                base_where,
                fs_alias.id.is_(None),
            )
        )
        pending = self.db.scalar(pending_stmt) or 0

        # Overdue subset
        overdue_stmt = (
            select(func.count())
            .select_from(Booking)
            .outerjoin(
                fs_alias,
                and_(
                    fs_alias.workspace_id == Booking.workspace_id,
                    fs_alias.booking_id == Booking.id,
                ),
            )
            .where(
                base_where,
                Booking.start_at < overdue_cutoff,
                fs_alias.id.is_(None),
            )
        )
        overdue = self.db.scalar(overdue_stmt) or 0

        return FormStats(pending=int(pending), overdue=int(overdue))

    # --- Inventory ---

    def _get_low_stock_items_model(
        self,
        workspace_id: UUID,
    ) -> list[InventoryItem]:
        return self.db.scalars(
            select(InventoryItem).where(
                InventoryItem.workspace_id == workspace_id,
                InventoryItem.is_deleted.is_(False),
                InventoryItem.reorder_threshold.is_not(None),
                InventoryItem.current_quantity < InventoryItem.reorder_threshold,
            )
        ).all()

    def _get_low_stock_items(
        self,
        workspace_id: UUID,
    ) -> list[InventoryLowStockItem]:
        items = self._get_low_stock_items_model(workspace_id)
        return [
            InventoryLowStockItem(
                id=i.id,
                sku=i.sku,
                name=i.name,
                current_quantity=i.current_quantity,
                reorder_threshold=i.reorder_threshold,
                unit=i.unit,
            )
            for i in items
        ]

    # --- Unanswered messages ---

    def _get_unanswered_conversations_count(
        self,
        workspace_id: UUID,
        min_age_minutes: int,
    ) -> int:
        cutoff = _utc_now() - timedelta(minutes=min_age_minutes)

        last_inbound_subq = (
            select(
                Message.conversation_id,
                func.max(Message.created_at).label("last_inbound_at"),
            )
            .where(
                Message.workspace_id == workspace_id,
                Message.direction == MessageDirection.inbound,
            )
            .group_by(Message.conversation_id)
            .subquery()
        )

        last_outbound_subq = (
            select(
                Message.conversation_id,
                func.max(Message.created_at).label("last_outbound_at"),
            )
            .where(
                Message.workspace_id == workspace_id,
                Message.direction == MessageDirection.outbound,
            )
            .group_by(Message.conversation_id)
            .subquery()
        )

        stmt = (
            select(func.count())
            .select_from(Conversation)
            .join(
                last_inbound_subq,
                last_inbound_subq.c.conversation_id == Conversation.id,
            )
            .outerjoin(
                last_outbound_subq,
                last_outbound_subq.c.conversation_id == Conversation.id,
            )
            .where(
                Conversation.workspace_id == workspace_id,
                Conversation.status == ConversationStatus.open,
                Conversation.automation_paused.is_(False),
                last_inbound_subq.c.last_inbound_at < cutoff,
                or_(
                    last_outbound_subq.c.last_outbound_at.is_(None),
                    last_outbound_subq.c.last_outbound_at
                    < last_inbound_subq.c.last_inbound_at,
                ),
            )
        )

        return int(self.db.scalar(stmt) or 0)

    # --- Alerts ---

    def _get_active_alerts(
        self,
        workspace_id: UUID,
        limit: int = 20,
    ) -> list[AlertSummary]:
        alerts = self.db.scalars(
            select(Alert)
            .where(
                Alert.workspace_id == workspace_id,
                Alert.acknowledged.is_(False),
                Alert.severity != AlertSeverity.info,
            )
            .order_by(Alert.created_at.desc())
            .limit(limit)
        ).all()

        return [
            AlertSummary(
                id=a.id,
                severity=a.severity,
                source=a.source,
                code=a.code,
                message=a.message,
                created_at=a.created_at,
            )
            for a in alerts
        ]