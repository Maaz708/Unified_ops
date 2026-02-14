import { cookies } from "next/headers";
import { getServerSession } from "@/lib/auth/session";
import { getDashboardOverview } from "@/lib/api/analytics";
import { BookingList } from "@/components/dashboard/BookingList";
import { StatCard } from "@/components/ui/StatCard";
import { AvailabilityManager } from "@/components/dashboard/AvailabilityManager";

export const dynamic = "force-dynamic";

export default async function BookingsPageContent() {
  const user = getServerSession();
  if (!user) return null;

  const token = cookies().get("auth_token")?.value ?? "";
  const overview = await getDashboardOverview(user.workspace_id);

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-4">
        <StatCard label="Today's bookings" value={overview.booking_stats.total_today} />
        <StatCard label="Upcoming" value={overview.booking_stats.total_upcoming} />
        <StatCard label="Completed" value={overview.booking_stats.completed} />
        <StatCard label="No-shows" value={overview.booking_stats.no_show} variant="warning" />
      </div>

      {user.role === "owner" && (
        <div className="card p-4">
          <AvailabilityManager workspaceId={user.workspace_id} token={token} />
        </div>
      )}

      <div className="card p-4 space-y-4">
        <h2 className="text-sm font-semibold text-slate-600">Today&apos;s bookings</h2>
        <p className="text-xs text-slate-500">Click a row to send confirmation. Use &quot;Mark completed&quot; or &quot;No-show&quot; when the appointment is done; the Completed count above will update after refresh.</p>
        <BookingList bookings={overview.today_bookings} workspaceId={user.workspace_id} token={token} />
      </div>

      <div className="card p-4 space-y-4">
        <h2 className="text-sm font-semibold text-slate-600">Upcoming bookings</h2>
        <BookingList bookings={overview.upcoming_bookings} workspaceId={user.workspace_id} token={token} />
      </div>

      <div className="card p-4 space-y-4">
        <h2 className="text-sm font-semibold text-slate-600">Booking history</h2>
        <p className="text-xs text-slate-500">Recent completed, no-show, and cancelled bookings (last 30 days).</p>
        <BookingList bookings={overview.recent_booking_history} workspaceId={user.workspace_id} token={token} showHistory />
      </div>
    </div>
  );
}

