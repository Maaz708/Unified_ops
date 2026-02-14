import type { NextApiRequest, NextApiResponse } from "next";

const RESEND_API_URL = "https://api.resend.com/emails";

async function sendEmailResend(params: {
  to: string;
  subject: string;
  text: string;
  from: string;
  apiKey: string;
}): Promise<{ ok: boolean; error?: string }> {
  const { to, subject, text, from, apiKey } = params;
  if (!apiKey) return { ok: false, error: "RESEND_API_KEY not set" };
  try {
    const res = await fetch(RESEND_API_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ from, to, subject, text }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) return { ok: false, error: (data as any).message || res.statusText };
    return { ok: true };
  } catch (e: any) {
    return { ok: false, error: e?.message || "Resend request failed" };
  }
}

const API_URL = process.env.NEXT_PUBLIC_API_URL?.replace(/\/?$/, "") || "http://localhost:8000/api/v1";
const BASE_URL = process.env.FRONTEND_URL || (process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : "http://localhost:3000");

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).end("Method Not Allowed");
  }

  const { workspaceId } = req.body;
  if (!workspaceId) {
    return res.status(400).json({ error: "Missing workspaceId" });
  }

  const token = req.cookies?.auth_token;
  if (!token) {
    return res.status(401).json({ error: "Not authenticated" });
  }

  let pending: Array<{
    booking_id: string;
    contact_id: string;
    contact_name: string | null;
    contact_email: string | null;
    form_template_id: string;
    form_name: string;
    booking_start_at: string;
  }>;
  try {
    const r = await fetch(
      `${API_URL}/workspaces/${workspaceId}/forms/pending-bookings`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    if (!r.ok) throw new Error(await r.text());
    pending = await r.json();
  } catch (e: any) {
    return res.status(502).json({ error: "Failed to fetch pending bookings", detail: e?.message });
  }

  const apiKey = process.env.RESEND_API_KEY;
  const fromEmail = process.env.RESEND_FROM_EMAIL || "onboarding@resend.dev";
  let sent = 0;
  const errors: string[] = [];

  for (const p of pending) {
    if (!p.contact_email?.trim()) continue;
    const formUrl = `${BASE_URL}/forms/complete?workspace=${encodeURIComponent(workspaceId)}&template=${encodeURIComponent(p.form_template_id)}&booking=${encodeURIComponent(p.booking_id)}&contact=${encodeURIComponent(p.contact_id)}`;
    const subject = `Reminder: complete your ${p.form_name}`;
    const text = `Hello ${p.contact_name || "there"},\n\nThis is a reminder to complete the form "${p.form_name}":\n${formUrl}\n\nThank you.`;
    const result = await sendEmailResend({
      apiKey: apiKey || "",
      from: fromEmail,
      to: p.contact_email.trim(),
      subject,
      text,
    });
    if (result.ok) sent++;
    else errors.push(`${p.contact_email}: ${result.error}`);
  }

  return res.status(200).json({
    message: `Sent ${sent} reminder(s)`,
    sent,
    total: pending.length,
    errors: errors.length ? errors : undefined,
  });
}
