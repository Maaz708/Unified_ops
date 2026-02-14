import clsx from "clsx";

export function StatCard({
  label,
  value,
  variant = "default"
}: {
  label: string;
  value: number | string;
  variant?: "default" | "warning";
}) {
  return (
    <div
      className={clsx(
        "card p-4",
        variant === "warning" && "border-amber-200 bg-amber-50/60"
      )}
    >
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
        {label}
      </p>
      <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}