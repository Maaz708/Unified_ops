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

const BASE_URL = process.env.FRONTEND_URL || (process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : "http://localhost:3000");

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).end("Method Not Allowed");
  }

  const { workspaceId, bookingId, contactId, contactName, contactEmail, formTemplateId } = req.body;

  if (!workspaceId || !bookingId || !contactId || !formTemplateId) {
    return res.status(400).json({ error: "Missing workspaceId, bookingId, contactId, or formTemplateId" });
  }
  if (!contactEmail?.trim()) {
    return res.status(400).json({ error: "contactEmail required to send form link" });
  }

  const formUrl = `${BASE_URL}/forms/complete?workspace=${encodeURIComponent(workspaceId)}&template=${encodeURIComponent(formTemplateId)}&booking=${encodeURIComponent(bookingId)}&contact=${encodeURIComponent(contactId)}`;
  const subject = "Complete your form";
  const text = `Hello ${contactName || "there"},\n\nPlease complete the following form:\n${formUrl}\n\nThank you.`;

  const apiKey = process.env.RESEND_API_KEY;
  const fromEmail = process.env.RESEND_FROM_EMAIL || "onboarding@resend.dev";

  const result = await sendEmailResend({
    apiKey: apiKey || "",
    from: fromEmail,
    to: contactEmail.trim(),
    subject,
    text,
  });

  if (!result.ok) {
    console.error("Resend error:", result.error);
    return res.status(500).json({ error: "Failed to send form link email", detail: result.error });
  }

  return res.status(200).json({ message: "Form link sent" });
}
