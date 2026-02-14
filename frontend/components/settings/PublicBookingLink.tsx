"use client";

import { useState } from "react";

export function PublicBookingLink({ workspaceId }: { workspaceId: string }) {
  const [copied, setCopied] = useState(false);
  // Use relative path for display so server and client match (avoids hydration error)
  const displayPath = `/book/${workspaceId}`;

  const copy = () => {
    const fullUrl =
      typeof window !== "undefined"
        ? `${window.location.origin}${displayPath}`
        : displayPath;
    navigator.clipboard.writeText(fullUrl).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="rounded-md border border-slate-200 bg-slate-50/50 p-3">
      <p className="text-xs font-medium text-slate-600">Public booking page (share with customers)</p>
      <div className="mt-2 flex gap-2">
        <code className="flex-1 truncate rounded bg-white px-2 py-1.5 text-sm text-slate-800">
          {displayPath}
        </code>
        <button
          type="button"
          onClick={copy}
          className="shrink-0 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
    </div>
  );
}
