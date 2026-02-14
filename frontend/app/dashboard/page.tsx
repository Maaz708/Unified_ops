import Link from "next/link";
import { cookies } from "next/headers";

export const dynamic = "force-dynamic";
import { getServerSession } from "@/lib/auth/session";
import { getDashboardOverview, getAiOperationalSummary } from "@/lib/api/analytics";
import { StatCard } from "@/components/ui/StatCard";
import { BookingList } from "@/components/dashboard/BookingList";
import { InventoryLowStockList } from "@/components/dashboard/InventoryLowStockList";
import { AlertsList } from "@/components/dashboard/AlertsList";
import { AiInsightCard } from "@/components/dashboard/AiInsightCard";
import type { DashboardOverview, AiOperationalSummary } from "@/lib/types/analytics";

const emptyOverview: DashboardOverview = {
  today_bookings: [],
  upcoming_bookings: [],
  recent_booking_history: [],
  booking_stats: { total_today: 0, total_upcoming: 0, completed: 0, no_show: 0 },
  form_stats: { pending: 0, overdue: 0 },
  low_stock_items: [],
  unanswered_conversations: 0,
  active_alerts: [],
};

const emptyAiSummary: AiOperationalSummary = {
  ok: true,
  overall_risk_level: "low",
  summary: "No data yet.",
  risks: [],
  recommendations: [],
};

export default async function DashboardPage() {
  const user = getServerSession();
  if (!user) return null;

  const token = (await cookies()).get("auth_token")?.value ?? "";
  let overview: DashboardOverview = emptyOverview;
  let aiSummary: AiOperationalSummary = emptyAiSummary;
  let overviewError = false;
  try {
    overview = await getDashboardOverview(user.workspace_id);
  } catch {
    overviewError = true;
  }
  try {
    aiSummary = await getAiOperationalSummary(user.workspace_id);
  } catch {
    // keep default
  }

  return (
    <div className="space-y-6">
      {overviewError && (
        <p className="rounded-md bg-amber-50 px-4 py-2 text-sm text-amber-800">
          Dashboard data could not be loaded. Check that the backend is running and your workspace is set up.
        </p>
      )}
      <div className="grid gap-4 md:grid-cols-4">
        <StatCard label="Today's bookings" value={overview.booking_stats.total_today} />
        <StatCard label="Upcoming" value={overview.booking_stats.total_upcoming} />
        <StatCard label="Completed" value={overview.booking_stats.completed} />
        <StatCard label="No-shows" value={overview.booking_stats.no_show} variant="warning" />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="card p-4 lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-600">Today&apos;s bookings</h2>
            <Link href="/dashboard/bookings" className="text-xs font-medium text-brand-600 hover:underline">View all</Link>
          </div>
          <BookingList bookings={overview.today_bookings} workspaceId={user.workspace_id} token={token} />
        </div>

        <AiInsightCard summary={aiSummary} />
      </div>

      <div className="card p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-600">Recent booking history</h2>
          <Link href="/dashboard/bookings" className="text-xs font-medium text-brand-600 hover:underline">View all</Link>
        </div>
        <BookingList bookings={overview.recent_booking_history} workspaceId={user.workspace_id} token={token} showHistory={true} />
      </div>

      <div className="grid gap-6 lg:grid-cols-4">
        <div className="card p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-600">Leads & conversations</h2>
            <Link href="/dashboard/inbox" className="text-xs font-medium text-brand-600 hover:underline">Inbox</Link>
          </div>
          <p className="text-sm text-slate-700">
            Unanswered: <span className="font-semibold">{overview.unanswered_conversations}</span>
          </p>
        </div>
        <div className="card p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-600">Low stock inventory</h2>
            <Link href="/dashboard/inventory" className="text-xs font-medium text-brand-600 hover:underline">View all</Link>
          </div>
          <InventoryLowStockList items={overview.low_stock_items} />
        </div>
        <div className="card p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-600">Pending / overdue forms</h2>
            <Link href="/dashboard/forms" className="text-xs font-medium text-brand-600 hover:underline">View all</Link>
          </div>
          <p className="text-sm text-slate-700">
            Pending: <span className="font-semibold">{overview.form_stats.pending}</span> • Overdue:{" "}
            <span className="font-semibold text-amber-600">{overview.form_stats.overdue}</span>
          </p>
        </div>
        <div className="card p-4 space-y-4">
          <h2 className="text-sm font-semibold text-slate-600">Active alerts</h2>
          <AlertsList alerts={overview.active_alerts} />
        </div>
      </div>
    </div>
  );
}
