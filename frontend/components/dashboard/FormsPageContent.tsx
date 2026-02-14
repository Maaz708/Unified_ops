"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  listFormTemplates,
  listFormSubmissions,
  createFormTemplate,
  updateFormTemplate,
  deleteFormTemplate,
  type FormTemplateOut,
  type FormSubmissionOut,
  type FormTemplateCreate,
  type FormTemplateUpdate,
} from "@/lib/api/forms";
import { listPublicBookingTypes, type PublicBookingType } from "@/lib/api/publicBooking";
import { request } from "@/lib/api/client";
import type { DashboardOverview } from "@/lib/types/analytics";

const DEFAULT_SCHEMA = { fields: [{ id: "q1", label: "Notes or special requests?", type: "text" }] };

// Function to create a readable summary of form schema
function getSchemaSummary(schema: any): string {
  try {
    const parsed = typeof schema === 'string' ? JSON.parse(schema) : schema;
    if (parsed?.fields && Array.isArray(parsed.fields)) {
      const fieldLabels = parsed.fields
        .map((field: any) => field.label || field.id || 'Unknown field')
        .filter((label: string) => label !== 'Unknown field');
      
      if (fieldLabels.length === 0) return 'No fields';
      if (fieldLabels.length === 1) return fieldLabels[0];
      if (fieldLabels.length === 2) return `${fieldLabels[0]} and ${fieldLabels[1]}`;
      return `${fieldLabels.slice(0, -1).join(', ')} and ${fieldLabels[fieldLabels.length - 1]}`;
    }
    return 'Custom form';
  } catch {
    return 'Custom form';
  }
}

export function FormsPageContent({
  workspaceId,
  token,
}: {
  workspaceId: string;
  token: string;
}) {
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [templates, setTemplates] = useState<FormTemplateOut[]>([]);
  const [submissions, setSubmissions] = useState<FormSubmissionOut[]>([]);
  const [bookingTypes, setBookingTypes] = useState<PublicBookingType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [createName, setCreateName] = useState("");
  const [createDesc, setCreateDesc] = useState("");
  const [createSchema, setCreateSchema] = useState(JSON.stringify(DEFAULT_SCHEMA, null, 2));
  const [createBookingTypeId, setCreateBookingTypeId] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [editing, setEditing] = useState<FormTemplateOut | null>(null);
  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const [editSchema, setEditSchema] = useState("");
  const [editBookingTypeId, setEditBookingTypeId] = useState("");
  const [editActive, setEditActive] = useState(true);
  const [contactUrlCopied, setContactUrlCopied] = useState(false);
  const [reminderLoading, setReminderLoading] = useState(false);
  const [reminderResult, setReminderResult] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [ov, tmpl, sub, bt] = await Promise.all([
        request<DashboardOverview>(`/analytics/workspaces/${workspaceId}/overview`, { token }),
        listFormTemplates(workspaceId, token),
        listFormSubmissions(workspaceId, token),
        listPublicBookingTypes(workspaceId),
      ]);
      setOverview(ov);
      setTemplates(tmpl);
      setSubmissions(sub);
      setBookingTypes(bt);
    } catch (e: any) {
      setError(e?.message ?? "Failed to load");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [workspaceId, token]);

  const handleCreate = async () => {
    if (!createName.trim()) return;
    setSubmitting(true);
    try {
      let schema: Record<string, unknown> = {};
      try {
        schema = JSON.parse(createSchema || "{}");
      } catch {
        setError("Invalid JSON for schema");
        setSubmitting(false);
        return;
      }
      const body: FormTemplateCreate = {
        name: createName.trim(),
        description: createDesc.trim() || null,
        schema,
        active: true,
        booking_type_id: createBookingTypeId || null,
      };
      await createFormTemplate(workspaceId, body, token);
      setShowCreate(false);
      setCreateName("");
      setCreateDesc("");
      setCreateSchema(JSON.stringify(DEFAULT_SCHEMA, null, 2));
      setCreateBookingTypeId("");
      await load();
    } catch (e: any) {
      setError(e?.message ?? "Create failed");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this form template?")) return;
    setDeletingId(id);
    try {
      await deleteFormTemplate(workspaceId, id, token);
      await load();
    } catch (e: any) {
      setError(e?.message ?? "Delete failed");
    } finally {
      setDeletingId(null);
    }
  };

  const startEdit = (t: FormTemplateOut) => {
    setEditing(t);
    setEditName(t.name);
    setEditDesc(t.description ?? "");
    setEditSchema(JSON.stringify(t.schema, null, 2));
    setEditBookingTypeId(t.booking_type_id ?? "");
    setEditActive(t.active);
  };

  const handleUpdate = async () => {
    if (!editing) return;
    setSubmitting(true);
    try {
      let schema: Record<string, unknown> = {};
      try {
        schema = JSON.parse(editSchema || "{}");
      } catch {
        setError("Invalid JSON for schema");
        setSubmitting(false);
        return;
      }
      const body: FormTemplateUpdate = {
        name: editName.trim(),
        description: editDesc.trim() || null,
        schema,
        active: editActive,
        booking_type_id: editBookingTypeId || null,
      };
      await updateFormTemplate(workspaceId, editing.id, body, token);
      setEditing(null);
      await load();
    } catch (e: any) {
      setError(e?.message ?? "Update failed");
    } finally {
      setSubmitting(false);
    }
  };

  const copyContactUrl = () => {
    const url =
      typeof window !== "undefined"
        ? `${window.location.origin}/contact/${workspaceId}`
        : "";
    if (url && typeof navigator !== "undefined") {
      navigator.clipboard.writeText(url);
      setContactUrlCopied(true);
      setTimeout(() => setContactUrlCopied(false), 2000);
    }
  };

  const sendReminders = async () => {
    setReminderLoading(true);
    setReminderResult(null);
    try {
      const res = await fetch("/api/send-form-reminders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ workspaceId }),
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        setReminderResult(`Sent ${(data as any).sent ?? 0} reminder(s).`);
        await load();
      } else {
        setReminderResult((data as any).error ?? "Failed to send reminders");
      }
    } catch (e: any) {
      setReminderResult(e?.message ?? "Request failed");
    } finally {
      setReminderLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12 text-slate-500">Loading…</div>
    );
  }

  const pending = overview?.form_stats?.pending ?? 0;
  const overdue = overview?.form_stats?.overdue ?? 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Forms</h1>
        <p className="mt-1 text-sm text-slate-600">
          Post-booking forms: intake, agreements, documents. Completion status is tracked here.
        </p>
        <p className="mt-1 text-xs text-slate-500">
          To have the form link sent to the customer&apos;s email: create a form, then set &quot;Link to booking type&quot; to the same type they book (e.g. Consultation). The form link is included with the confirmation when they book and when you send confirmation from Bookings.
        </p>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 px-4 py-2 text-sm text-red-700">{error}</div>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Link href="#submissions" className="card p-4 hover:border-brand-300">
          <h2 className="text-sm font-semibold text-slate-600">Pending</h2>
          <p className="mt-1 text-2xl font-semibold text-slate-900">{pending}</p>
          <p className="mt-1 text-xs text-slate-500">Bookings awaiting form completion</p>
        </Link>
        <Link href="#submissions" className="card p-4 hover:border-amber-300">
          <h2 className="text-sm font-semibold text-slate-600">Overdue</h2>
          <p className="mt-1 text-2xl font-semibold text-amber-600">{overdue}</p>
          <p className="mt-1 text-xs text-slate-500">Past due date</p>
        </Link>
        <div className="card p-4">
          <h2 className="text-sm font-semibold text-slate-600">Form templates</h2>
          <p className="mt-1 text-sm text-slate-600">
            Create and link forms to booking types below.
          </p>
        </div>
        <div className="card p-4">
          <h2 className="text-sm font-semibold text-slate-600">Contact form</h2>
          <p className="mt-1 text-xs text-slate-500">Public page for leads</p>
          <p className="mt-1 truncate font-mono text-xs text-slate-600">/contact/{workspaceId}</p>
          <button
            type="button"
            onClick={copyContactUrl}
            className="mt-2 text-sm font-medium text-brand-600 hover:underline"
          >
            {contactUrlCopied ? "Copied!" : "Copy full URL"}
          </button>
        </div>
      </div>

      <section className="card p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium text-slate-900">Form templates</h2>
          <button
            type="button"
            onClick={() => setShowCreate((s) => !s)}
            className="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700"
          >
            {showCreate ? "Cancel" : "Create form"}
          </button>
        </div>
        {showCreate && (
          <div className="mt-4 space-y-3 rounded-lg border border-slate-200 bg-slate-50/50 p-4">
            <div>
              <label className="block text-sm font-medium text-slate-700">Name</label>
              <input
                type="text"
                value={createName}
                onChange={(e) => setCreateName(e.target.value)}
                className="mt-1 w-full max-w-md rounded border border-slate-300 px-2 py-1.5 text-sm"
                placeholder="e.g. Intake form"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Description (optional)</label>
              <input
                type="text"
                value={createDesc}
                onChange={(e) => setCreateDesc(e.target.value)}
                className="mt-1 w-full max-w-md rounded border border-slate-300 px-2 py-1.5 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">
                Link to booking type (optional)
              </label>
              <select
                value={createBookingTypeId}
                onChange={(e) => setCreateBookingTypeId(e.target.value)}
                className="mt-1 rounded border border-slate-300 px-2 py-1.5 text-sm"
              >
                <option value="">— None —</option>
                {bookingTypes.map((bt) => (
                  <option key={bt.id} value={bt.id}>
                    {bt.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Form fields</label>
              <div className="mt-1 text-sm text-slate-600">
                {getSchemaSummary(createSchema)}
              </div>
            </div>
            <button
              type="button"
              onClick={handleCreate}
              disabled={submitting}
              className="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
            >
              {submitting ? "Creating…" : "Create"}
            </button>
          </div>
        )}
        <ul className="mt-4 space-y-2">
          {templates.length === 0 && !showCreate && (
            <li className="text-sm text-slate-500">No form templates yet. Create one above.</li>
          )}
          {templates.map((t) => (
            <li
              key={t.id}
              className="flex items-center justify-between rounded border border-slate-200 bg-white px-3 py-2"
            >
              <div>
                <span className="font-medium text-slate-900">{t.name}</span>
                {t.description && (
                  <span className="ml-2 text-sm text-slate-500">{t.description}</span>
                )}
                {t.booking_type_id && (
                  <span className="ml-2 text-xs text-slate-400">
                    (linked to booking type)
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">{t.active ? "Active" : "Inactive"}</span>
                <button
                  type="button"
                  onClick={() => startEdit(t)}
                  className="text-sm text-brand-600 hover:underline"
                >
                  Edit
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(t.id)}
                  disabled={deletingId === t.id}
                  className="text-sm text-red-600 hover:underline disabled:opacity-50"
                >
                  {deletingId === t.id ? "Deleting…" : "Delete"}
                </button>
              </div>
            </li>
          ))}
        </ul>
        {editing && (
          <div className="mt-4 space-y-3 rounded-lg border border-slate-200 bg-amber-50/50 p-4">
            <h3 className="font-medium text-slate-900">Edit: {editing.name}</h3>
            <div>
              <label className="block text-sm font-medium text-slate-700">Name</label>
              <input
                type="text"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                className="mt-1 w-full max-w-md rounded border border-slate-300 px-2 py-1.5 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Description (optional)</label>
              <input
                type="text"
                value={editDesc}
                onChange={(e) => setEditDesc(e.target.value)}
                className="mt-1 w-full max-w-md rounded border border-slate-300 px-2 py-1.5 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Link to booking type</label>
              <select
                value={editBookingTypeId}
                onChange={(e) => setEditBookingTypeId(e.target.value)}
                className="mt-1 rounded border border-slate-300 px-2 py-1.5 text-sm"
              >
                <option value="">— None —</option>
                {bookingTypes.map((bt) => (
                  <option key={bt.id} value={bt.id}>
                    {bt.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="edit-active"
                checked={editActive}
                onChange={(e) => setEditActive(e.target.checked)}
              />
              <label htmlFor="edit-active" className="text-sm text-slate-700">Active</label>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Form fields</label>
              <div className="mt-1 text-sm text-slate-600">
                {getSchemaSummary(editSchema)}
              </div>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={handleUpdate}
                disabled={submitting}
                className="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
              >
                {submitting ? "Saving…" : "Save"}
              </button>
              <button
                type="button"
                onClick={() => setEditing(null)}
                className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </section>

      <section id="submissions" className="card p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="text-lg font-medium text-slate-900">Form submissions</h2>
            <p className="mt-1 text-sm text-slate-600">
              Completed form submissions. Pending/overdue counts above refer to bookings without a submission.
            </p>
            <p className="mt-1 text-xs text-slate-500">
              To see what the customer wrote and reply by email, go to <Link href="/dashboard/inbox" className="font-medium text-brand-600 hover:underline">Inbox</Link> — each form submission appears there as a message from the contact.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={sendReminders}
              disabled={reminderLoading || (pending === 0 && overdue === 0)}
              className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            >
              {reminderLoading ? "Sending…" : "Send reminder emails"}
            </button>
            {reminderResult && (
              <span className="text-sm text-slate-600">{reminderResult}</span>
            )}
          </div>
        </div>
        <div className="mt-4 overflow-x-auto">
          {submissions.length === 0 ? (
            <p className="text-sm text-slate-500">No submissions yet.</p>
          ) : (
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead>
                <tr>
                  <th className="py-2 text-left font-medium text-slate-700">Submitted</th>
                  <th className="py-2 text-left font-medium text-slate-700">Form</th>
                  <th className="py-2 text-left font-medium text-slate-700">Booking</th>
                  <th className="py-2 text-left font-medium text-slate-700">Contact</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {submissions.map((s) => (
                  <tr key={s.id}>
                    <td className="py-2 text-slate-600" suppressHydrationWarning>
                      {new Date(s.submitted_at).toLocaleString()}
                    </td>
                    <td className="py-2">
                      {templates.find((t) => t.id === s.form_template_id)?.name ?? s.form_template_id}
                    </td>
                    <td className="py-2 font-mono text-xs">{s.booking_id}</td>
                    <td className="py-2 font-mono text-xs">{s.contact_id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>
    </div>
  );
}
