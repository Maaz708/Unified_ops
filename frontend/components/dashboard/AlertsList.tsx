import Link from "next/link";
import type { AlertSummary } from "@/lib/types/analytics";

function alertHref(alert: AlertSummary): string {
  const code = (alert.code || "").toLowerCase();
  if (code.includes("message") || code.includes("inbox") || code.includes("conversation")) return "/dashboard/inbox";
  if (code.includes("booking") || code.includes("unconfirmed")) return "/dashboard/bookings";
  if (code.includes("form") || code.includes("overdue")) return "/dashboard/forms";
  if (code.includes("inventory") || code.includes("stock")) return "/dashboard/inventory";
  return "/dashboard";
}

export function AlertsList({ alerts }: { alerts: AlertSummary[] }) {
  if (!alerts.length) {
    return <p className="text-sm text-slate-500">No active alerts.</p>;
  }

  return (
    <ul className="space-y-2 text-sm">
      {alerts.map((a) => {
        const href = alertHref(a);
        return (
          <li key={a.id}>
            <Link
              href={href}
              className="block rounded-md border border-slate-200 bg-slate-50 px-3 py-2 hover:bg-slate-100"
            >
              <div className="flex justify-between">
                <span className="font-medium text-slate-800">{a.code}</span>
                <span className="text-xs uppercase text-slate-500">{a.severity}</span>
              </div>
              <p className="mt-1 text-xs text-slate-700">{a.message}</p>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}