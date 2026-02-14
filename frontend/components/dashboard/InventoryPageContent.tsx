import { getServerSession } from "@/lib/auth/session";
import { getDashboardOverview } from "@/lib/api/analytics";
import { getInventoryList } from "@/lib/api/inventory";
import { StatCard } from "@/components/ui/StatCard";
import { cookies } from "next/headers";

export default async function InventoryPageContent() {
  const user = getServerSession();
  if (!user) return null;

  const cookieStore = cookies();
  const token = cookieStore.get("auth_token")?.value ?? "";

  const overview = await getDashboardOverview(user.workspace_id);
  const inventory = await getInventoryList(user.workspace_id, token);

  const totalSkus = inventory.length;
  const totalQuantity = inventory.reduce((sum, i) => sum + (i.current_quantity || 0), 0);

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-4">
        <StatCard label="Low-stock items" value={overview.low_stock_items.length} variant="warning" />
        <StatCard label="Total items" value={totalSkus} />
        <StatCard label="Total quantity" value={totalQuantity} />
        <StatCard label="Today&apos;s bookings" value={overview.booking_stats.total_today} />
        <StatCard label="Active alerts" value={overview.active_alerts.length} />
      </div>

      <div className="card p-4 space-y-4">
        <h2 className="text-sm font-semibold text-slate-600">All inventory</h2>
        {inventory.length === 0 ? (
          <p className="text-sm text-slate-500">No inventory items yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">SKU</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Name</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Quantity</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Unit</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Reorder at</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-200">
                {inventory.map((item) => {
                  const isLow = item.reorder_threshold && item.current_quantity <= item.reorder_threshold;
                  return (
                    <tr key={item.id} className={isLow ? "bg-red-50" : ""}>
                      <td className="px-4 py-2 text-sm text-slate-900">{item.sku}</td>
                      <td className="px-4 py-2 text-sm text-slate-900">{item.name}</td>
                      <td className="px-4 py-2 text-sm text-slate-900">{item.current_quantity}</td>
                      <td className="px-4 py-2 text-sm text-slate-500">{item.unit || "-"}</td>
                      <td className="px-4 py-2 text-sm text-slate-500">{item.reorder_threshold ?? "-"}</td>
                      <td className="px-4 py-2">
                        {isLow ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                            Low stock
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                            OK
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

