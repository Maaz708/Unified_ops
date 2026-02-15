import type { NextApiRequest, NextApiResponse } from "next";

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).end("Method Not Allowed");
  }

  try {
    // Resend inbound email webhook payload
    const { from, to, subject, text, html, headers } = req.body;
    
    console.log("Received email reply:", { from, to, subject, text: text?.substring(0, 100) });

    // Extract email from "from" field (format: "Name <email@domain.com>")
    const emailMatch = from.match(/<(.+)>/);
    const customerEmail = emailMatch ? emailMatch[1] : from;
    
    // Extract conversation ID from the "to" address or subject
    // You might need to encode conversation ID in the reply-to address
    const conversationMatch = subject.match(/ID: ([a-f0-9-]+)/);
    const conversationId = conversationMatch ? conversationMatch[1] : null;

    if (!conversationId) {
      console.error("No conversation ID found in email");
      return res.status(400).json({ error: "No conversation ID found" });
    }

    // Add the reply to the conversation in your database
    // This would connect to your backend to add the message
    const response = await fetch(`${process.env.API_URL || 'http://localhost:8000'}/api/v1/conversations/${conversationId}/messages`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        content: text,
        direction: "inbound",
        channel: "email",
        customer_email: customerEmail,
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      console.error("Failed to add message to conversation:", error);
      return res.status(500).json({ error: "Failed to add message to conversation" });
    }

    console.log("Successfully added email reply to conversation:", conversationId);
    return res.status(200).json({ message: "Email reply processed successfully" });

  } catch (error) {
    console.error("Webhook error:", error);
    return res.status(500).json({ error: "Internal server error" });
  }
}
