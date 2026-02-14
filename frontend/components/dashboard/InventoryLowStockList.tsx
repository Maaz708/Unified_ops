import type { LowStockItem } from "@/lib/types/inventory";
import { Table } from "@/components/ui/Table";

export function InventoryLowStockList({ items }: { items: LowStockItem[] }) {
  if (!items.length) {
    return <p className="text-sm text-slate-500">No low-stock items 🎉</p>;
  }

  return (
    <Table>
      <thead className="bg-slate-50">
        <tr>
          <th className="px-4 py-2 text-left text-xs font-medium text-slate-500">Item</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-slate-500">SKU</th>
          <th className="px-4 py-2 text-right text-xs font-medium text-slate-500">Qty</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-slate-100 bg-white text-sm">
        {items.map((i) => (
          <tr key={i.id}>
            <td className="px-4 py-2 text-slate-800">{i.name}</td>
            <td className="px-4 py-2 text-slate-600">{i.sku}</td>
            <td className="px-4 py-2 text-right text-amber-700">
              {i.current_quantity} {i.unit}
            </td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}