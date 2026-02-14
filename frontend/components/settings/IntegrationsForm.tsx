"use client";

import { useEffect, useState } from "react";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import {
  getWorkspaceEmailConfig,
  updateWorkspaceEmailConfig,
  type WorkspaceEmailConfigOut,
} from "@/lib/api/workspace";

export function IntegrationsForm({
  workspaceId,
  token,
}: {
  workspaceId: string;
  token: string;
}) {
  const [config, setConfig] = useState<WorkspaceEmailConfigOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fromEmail, setFromEmail] = useState("");
  const [fromName, setFromName] = useState("");
  const [apiKeyAlias, setApiKeyAlias] = useState("");

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    getWorkspaceEmailConfig(workspaceId, token)
      .then((c) => {
        setConfig(c);
        setFromEmail(c.from_email);
        setFromName(c.from_name ?? "");
        setApiKeyAlias(c.api_key_alias);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [workspaceId, token]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await updateWorkspaceEmailConfig(
        workspaceId,
        { from_email: fromEmail, from_name: fromName || null, api_key_alias: apiKeyAlias },
        token
      );
      setConfig(updated);
    } catch (e: any) {
      setError(e.message ?? "Save failed");
    } finally {
      setSaving(false);
    }
  }

  if (!token) {
    return (
      <p className="text-sm text-slate-500">Sign in again to manage integrations.</p>
    );
  }

  if (loading) {
    return <p className="text-sm text-slate-500">Loading…</p>;
  }

  if (error && !config) {
    return <p className="text-sm text-red-600">{error}</p>;
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="rounded-md border border-slate-200 bg-slate-50/50 p-4">
        <h3 className="text-sm font-semibold text-slate-700">Email (Resend)</h3>
        <p className="mt-1 text-xs text-slate-500">
          Confirmations and alerts are sent from this address. At least one channel is required.
        </p>
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          <Input
            label="From email"
            type="email"
            value={fromEmail}
            onChange={(e) => setFromEmail(e.target.value)}
            required
          />
          <Input
            label="From name"
            type="text"
            value={fromName}
            onChange={(e) => setFromName(e.target.value)}
            placeholder="Your business name"
          />
          <Input
            label="API key alias"
            type="text"
            value={apiKeyAlias}
            onChange={(e) => setApiKeyAlias(e.target.value)}
            placeholder="default-resend"
          />
        </div>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        <Button type="submit" className="mt-3" disabled={saving}>
          {saving ? "Saving…" : "Save email settings"}
        </Button>
      </div>
      <div className="rounded-md border border-dashed border-slate-200 bg-slate-50/30 p-4">
        <h3 className="text-sm font-semibold text-slate-700">SMS (e.g. Twilio)</h3>
        <p className="mt-1 text-xs text-slate-500">
          Reminders and short updates. Configuration UI coming soon; failures are logged.
        </p>
      </div>
    </form>
  );
}
