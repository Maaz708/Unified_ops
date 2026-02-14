"use client";

import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/?$/, "") || "http://localhost:8000/api/v1";

type FormField = { id: string; label?: string; type?: string };
type Schema = { fields?: FormField[] };

export default function FormCompletePage() {
  const searchParams = useSearchParams();
  const workspaceId = searchParams.get("workspace") ?? "";
  const templateId = searchParams.get("template") ?? "";
  const bookingId = searchParams.get("booking") ?? "";
  const contactId = searchParams.get("contact") ?? "";

  const [template, setTemplate] = useState<{ id: string; name: string; schema: Schema } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const load = useCallback(async () => {
    if (!workspaceId || !templateId) {
      setLoading(false);
      setError("Missing workspace or form in the link.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `${API_URL}/public/${workspaceId}/forms/${templateId}`
      );
      if (!res.ok) {
        if (res.status === 404) setError("Form not found or no longer available.");
        else setError("Failed to load form.");
        return;
      }
      const data = await res.json();
      setTemplate(data);
    } catch {
      setError("Failed to load form.");
    } finally {
      setLoading(false);
    }
  }, [workspaceId, templateId]);

  useEffect(() => {
    load();
  }, [load]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!workspaceId || !templateId || !bookingId || !contactId) {
      setError("Invalid form link (missing parameters).");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch(
        `${API_URL}/public/${workspaceId}/forms/submit`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            template_id: templateId,
            booking_id: bookingId,
            contact_id: contactId,
            answers,
          }),
        }
      );
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        if (res.status === 409) {
          setError("This form has already been submitted.");
          return;
        }
        throw new Error((data as any).detail ?? res.statusText);
      }
      setSubmitted(true);
    } catch (e: any) {
      setError(e?.message ?? "Submission failed.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="mx-auto max-w-lg px-4 py-12 text-center text-slate-600">
        Loading form…
      </div>
    );
  }

  if (error && !template) {
    return (
      <div className="mx-auto max-w-lg px-4 py-12">
        <h1 className="text-xl font-semibold text-slate-900">Form</h1>
        <p className="mt-2 text-slate-600">{error}</p>
      </div>
    );
  }

  if (submitted) {
    return (
      <div className="mx-auto max-w-lg px-4 py-12 text-center">
        <h1 className="text-xl font-semibold text-slate-900">Thank you</h1>
        <p className="mt-2 text-slate-600">Your responses have been submitted.</p>
      </div>
    );
  }

  const fields = template?.schema?.fields ?? [];

  return (
    <div className="mx-auto max-w-lg px-4 py-12">
      <h1 className="text-xl font-semibold text-slate-900">{template?.name ?? "Form"}</h1>
      <p className="mt-1 text-sm text-slate-600">Please complete the following.</p>
      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        {error && (
          <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}
        {fields.map((f) => (
          <div key={f.id}>
            {f.type === "textarea" ? (
              <>
                <label className="block text-sm font-medium text-slate-700">
                  {f.label ?? f.id}
                </label>
                <textarea
                  value={answers[f.id] ?? ""}
                  onChange={(e) =>
                    setAnswers((a) => ({ ...a, [f.id]: e.target.value }))
                  }
                  rows={4}
                  className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
                />
              </>
            ) : (
              <Input
                label={f.label ?? f.id}
                type={f.type === "number" ? "number" : "text"}
                value={answers[f.id] ?? ""}
                onChange={(e) =>
                  setAnswers((a) => ({ ...a, [f.id]: e.target.value }))
                }
              />
            )}
          </div>
        ))}
        {fields.length === 0 && (
          <p className="text-sm text-slate-500">This form has no fields.</p>
        )}
        <Button type="submit" disabled={submitting}>
          {submitting ? "Submitting…" : "Submit"}
        </Button>
      </form>
    </div>
  );
}
