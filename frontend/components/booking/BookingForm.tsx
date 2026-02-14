"use client";

import { useState } from "react";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { createPublicBooking } from "@/lib/api/booking";

export function BookingForm({ workspaceId }: { workspaceId: string }) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setResult(null);
    try {
      // In full implementation you’d pass selected booking_type_slug + start/end
      await createPublicBooking({
        workspaceId,
        booking_type_slug: "default",
        start_at: new Date().toISOString(),
        end_at: new Date(Date.now() + 30 * 60 * 1000).toISOString(),
        full_name: fullName,
        email,
        phone
      });
      setResult("Booking created! Check your email for confirmation.");
    } catch (err: any) {
      setResult(err.message || "Booking failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <h2 className="text-sm font-semibold text-slate-700">Your details</h2>
      <Input label="Full name" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
      <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
      <Input label="Phone" value={phone} onChange={(e) => setPhone(e.target.value)} />
      <Button type="submit" className="w-full" disabled={submitting}>
        {submitting ? "Booking..." : "Confirm booking"}
      </Button>
      {result && <p className="text-xs text-slate-600">{result}</p>}
    </form>
  );
}