"use client";

import type { AiOperationalSummary } from "@/lib/types/analytics";
import { Badge } from "@/components/ui/Badge";

const riskColor: Record<string, string> = {
  low: "bg-emerald-50 text-emerald-800",
  medium: "bg-amber-50 text-amber-800",
  high: "bg-orange-50 text-orange-800",
  critical: "bg-red-50 text-red-800"
};

export function AiInsightCard({ summary }: { summary: AiOperationalSummary }) {
  const level = summary.overall_risk_level.toLowerCase();
  const badgeClass = riskColor[level] ?? "bg-slate-100 text-slate-800";

  return (
    <div className="card h-full p-4 flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-sm font-semibold text-slate-700">AI Operational Insight</h2>
        <Badge className={badgeClass}>{summary.overall_risk_level}</Badge>
      </div>
      <p className="text-sm text-slate-700 mb-3">{summary.summary}</p>
      {!summary.ok && (
        <p className="text-xs text-slate-500">
          AI is temporarily unavailable. Showing metrics only.
        </p>
      )}
    </div>
  );
}