import type { BookingCard } from "./booking";
import type { LowStockItem } from "./inventory";

export interface BookingStats {
  total_today: number;
  total_upcoming: number;
  completed: number;
  no_show: number;
}

export interface FormStats {
  pending: number;
  overdue: number;
}

export interface AlertSummary {
  id: string;
  severity: string;
  source: string;
  code: string;
  message: string;
  created_at: string;
}

export interface DashboardOverview {
  today_bookings: BookingCard[];
  upcoming_bookings: BookingCard[];
  recent_booking_history: BookingCard[];
  booking_stats: BookingStats;
  form_stats: FormStats;
  low_stock_items: LowStockItem[];
  unanswered_conversations: number;
  active_alerts: AlertSummary[];
}

export interface AiOperationalSummary {
  ok: boolean;
  overall_risk_level: string;
  summary: string;
  risks: any;
  recommendations: any;
}
