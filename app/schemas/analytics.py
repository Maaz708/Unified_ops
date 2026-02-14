# app/schemas/analytics.py
from datetime import datetime
from typing import List, Optional, Any

from pydantic import BaseModel, ConfigDict
from uuid import UUID

from app.models.booking import BookingStatus
from app.models.alert import AlertSeverity, AlertSource


class BookingCard(BaseModel):
    id: UUID
    start_at: datetime
    end_at: datetime
    status: BookingStatus
    contact_name: Optional[str]
    booking_type_name: Optional[str]
    contact_id: Optional[UUID] = None
    primary_email: Optional[str] = None
    primary_phone: Optional[str] = None


class BookingStats(BaseModel):
    total_today: int
    total_upcoming: int
    completed: int
    no_show: int


class FormStats(BaseModel):
    pending: int
    overdue: int


class InventoryLowStockItem(BaseModel):
    id: UUID
    sku: str
    name: str
    current_quantity: int
    reorder_threshold: Optional[int]
    unit: Optional[str]


class AlertSummary(BaseModel):
    id: UUID
    severity: AlertSeverity
    source: AlertSource
    code: str
    message: str
    created_at: datetime


class DashboardOverview(BaseModel):
    today_bookings: List[BookingCard]
    upcoming_bookings: List[BookingCard]
    recent_booking_history: List[BookingCard]
    booking_stats: BookingStats
    form_stats: FormStats
    low_stock_items: List[InventoryLowStockItem]
    unanswered_conversations: int
    active_alerts: List[AlertSummary]


class AiOperationalSummary(BaseModel):
    ok: bool
    overall_risk_level: str
    summary: str
    risks: Any
    recommendations: Any