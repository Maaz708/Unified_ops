import { getServerSession } from "@/lib/auth/session";
import { getDashboardOverview, getAiOperationalSummary } from "@/lib/api/analytics";
import { StatCard } from "@/components/ui/StatCard";
import { BookingList } from "@/components/dashboard/BookingList";
import { InventoryLowStockList } from "@/components/dashboard/InventoryLowStockList";
import { AlertsList } from "@/components/dashboard/AlertsList";
import { AiInsightCard } from "@/components/dashboard/AiInsightCard";

export default async function AnalyticsPageContent() {
  const user = getServerSession();
  if (!user) return null;

  const overview = await getDashboardOverview(user.workspace_id);
  const aiSummary = await getAiOperationalSummary(user.workspace_id);

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-4">
        <StatCard label="Today's bookings" value={overview.booking_stats.total_today} />
        <StatCard label="Upcoming" value={overview.booking_stats.total_upcoming} />
        <StatCard label="Completed" value={overview.booking_stats.completed} />
        <StatCard label="No-shows" value={overview.booking_stats.no_show} variant="warning" />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="card p-4 lg:col-span-2 space-y-4">
          <h2 className="text-sm font-semibold text-slate-600">Today&apos;s bookings</h2>
          <BookingList bookings={overview.today_bookings} />
        </div>

        <AiInsightCard summary={aiSummary} />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="card p-4 space-y-4">
          <h2 className="text-sm font-semibold text-slate-600">Low stock inventory</h2>
          <InventoryLowStockList items={overview.low_stock_items} />
        </div>
        <div className="card p-4 space-y-4">
          <h2 className="text-sm font-semibold text-slate-600">Form performance</h2>
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

