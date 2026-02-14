"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";

export function ReplyBox({ onSend }: { onSend: (body: string) => Promise<void> }) {
  const [value, setValue] = useState("");
  const [sending, setSending] = useState(false);

  async function handleSend() {
    if (!value.trim()) return;
    setSending(true);
    try {
      await onSend(value.trim());
      setValue("");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="border-t border-slate-200 pt-3">
      <textarea
        rows={3}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        className="w-full resize-none rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
        placeholder="Type a reply..."
      />
      <div className="mt-2 flex justify-end">
        <Button onClick={handleSend} disabled={sending || !value.trim()}>
          {sending ? "Sending..." : "Send"}
        </Button>
      </div>
    </div>
  );
}