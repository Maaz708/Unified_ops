import type { NextApiRequest, NextApiResponse } from "next";

const RESEND_API_URL = "https://api.resend.com/emails";

async function sendEmailResend(params: {
  to: string;
  subject: string;
  text: string;
  from: string;
  apiKey: string;
  replyTo?: string;
}): Promise<{ ok: boolean; id?: string; error?: string }> {
  const { to, subject, text, from, apiKey, replyTo } = params;
  if (!apiKey) return { ok: false, error: "RESEND_API_KEY not set" };
  try {
    const emailBody = {
      from,
      to,
      subject,
      text,
      ...(replyTo && { replyTo: replyTo }),
    };
    
    const res = await fetch(RESEND_API_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(emailBody),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) return { ok: false, error: (data as any).message || res.statusText };
    return { ok: true, id: (data as any).id };
  } catch (e: any) {
    return { ok: false, error: e?.message || "Resend request failed" };
  }
}

async function sendSmsTwilio(phoneNumber: string, message: string): Promise<{ ok: boolean; error?: string }> {
  const accountSid = process.env.TWILIO_ACCOUNT_SID;
  const authToken = process.env.TWILIO_AUTH_TOKEN;
  const from = process.env.TWILIO_PHONE_NUMBER;
  if (!accountSid || !authToken || !from) return { ok: false, error: "Twilio not configured" };
  try {
    const res = await fetch(
      `https://api.twilio.com/2010-04-01/Accounts/${accountSid}/Messages.json`,
      {
        method: "POST",
        headers: {
          Authorization: "Basic " + Buffer.from(`${accountSid}:${authToken}`).toString("base64"),
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({ To: phoneNumber, From: from, Body: message }),
      }
    );
    const data = await res.json().catch(() => ({}));
    if (!res.ok) return { ok: false, error: (data as any).message || res.statusText };
    return { ok: true };
  } catch (e: any) {
    return { ok: false, error: e?.message || "Twilio request failed" };
  }
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).end("Method Not Allowed");
  }

  const { bookingId, contactName, email, phoneNumber, startAt } = req.body;

  console.log("Email confirmation request:", { bookingId, contactName, email, phoneNumber, startAt });

  if (!bookingId || !contactName || (!email && !phoneNumber) || !startAt) {
    console.log("Missing required fields:", { bookingId, contactName, email, phoneNumber, startAt });
    return res.status(400).json({ error: "Missing required fields" });
  }

  const startTime = new Date(startAt).toLocaleString();
  // Use your personal email to receive replies
  const replyToEmail = process.env.REPLY_TO_EMAIL || "your-email@gmail.com";
  const text = `Hello ${contactName},\n\nYour booking (ID: ${bookingId}) is confirmed for ${startTime}.\n\nPlease reply to this email if you have any questions!\n\nThank you!`;
  const subject = `Booking Confirmation - ID: ${bookingId}`;

  const apiKey = process.env.RESEND_API_KEY;
  const fromEmail = process.env.RESEND_FROM_EMAIL || "onboarding@resend.dev";

  console.log("Environment check:", { 
    hasApiKey: !!apiKey, 
    apiKeyPrefix: apiKey?.substring(0, 10) + "...",
    fromEmail 
  });

  if (email) {
    const result = await sendEmailResend({
      apiKey: apiKey || "",
      from: fromEmail,
      to: email,
      subject,
      text,
      replyTo: replyToEmail,
    });
    if (!result.ok) {
      console.error("Resend error:", result.error);
      return res.status(500).json({ error: "Failed to send email", detail: result.error });
    }
  }

  if (phoneNumber) {
    const smsMessage = `Hello ${contactName}, your booking (ID: ${bookingId}) is confirmed for ${startTime}.`;
    const result = await sendSmsTwilio(phoneNumber, smsMessage);
    if (!result.ok) {
      console.error("Twilio error:", result.error);
      if (!email) return res.status(500).json({ error: "Failed to send SMS", detail: result.error });
    }
  }

  return res.status(200).json({ message: "Confirmation sent successfully" });
}
