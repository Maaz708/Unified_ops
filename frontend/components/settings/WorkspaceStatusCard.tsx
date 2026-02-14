"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import {
  getWorkspaceStatus,
  activateWorkspace,
  type WorkspaceStatusResponse,
} from "@/lib/api/workspace";

const REASON_LABELS: Record<string, string> = {
  EMAIL_PROVIDER_NOT_CONNECTED: "Connect email in Step 2 (Settings → Email & SMS).",
  NO_BOOKING_TYPES: "Add at least one booking type (Step 4).",
  NO_AVAILABILITY_DEFINED: "Define availability for your booking types (Step 4).",
};

export function WorkspaceStatusCard({
  workspaceId,
  token,
}: {
  workspaceId: string;
  token: string;
}) {
  const [data, setData] = useState<WorkspaceStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activating, setActivating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    getWorkspaceStatus(workspaceId, token)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, [workspaceId, token]);

  const handleActivate = () => {
    if (!token) return;
    setActivating(true);
    setError(null);
    activateWorkspace(workspaceId, token)
      .then(setData)
      .catch((e) => {
        const msg = e.message || (typeof e.detail === "string" ? e.detail : "Activation failed.");
        setError(msg);
      })
      .finally(() => setActivating(false));
  };

  if (!token) {
    return (
      <p className="text-sm text-slate-500">Sign in to see workspace status.</p>
    );
  }

  if (loading && !data) {
    return <p className="text-sm text-slate-500">Loading status…</p>;
  }

  if (error && !data) {
    return <p className="text-sm text-red-600">{error}</p>;
  }

  if (!data) return null;

  const isActive = data.status === "active";
  const v = data.validation;

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="font-medium text-slate-900">
            Workspace is {isActive ? "active" : "not active"}
          </p>
          <p className="mt-1 text-sm text-slate-600">
            {isActive
              ? "Public booking page and automations are live."
              : "Complete the steps above, then click Activate. Until then, the public booking link will not work."}
          </p>
        </div>
        {!isActive && v.can_activate && (
          <Button onClick={handleActivate} disabled={activating}>
            {activating ? "Activating…" : "Activate workspace"}
          </Button>
        )}
      </div>
      {!isActive && v.reasons && v.reasons.length > 0 && (
        <ul className="mt-3 space-y-1 text-sm text-amber-800">
          {v.reasons.map((r) => (
            <li key={r}>• {REASON_LABELS[r] ?? r}</li>
          ))}
        </ul>
      )}
      {error && (
        <p className="mt-2 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
}
