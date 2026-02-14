"use client";

import type { ReactNode } from "react";
import clsx from "clsx";

interface Tab {
  id: string;
  label: string;
}

export function Tabs({
  tabs,
  active,
  onChange
}: {
  tabs: Tab[];
  active: string;
  onChange: (id: string) => void;
}) {
  return (
    <div className="inline-flex rounded-lg border border-slate-200 bg-slate-100 p-1 text-xs">
      {tabs.map((t) => (
        <button
          key={t.id}
          onClick={() => onChange(t.id)}
          className={clsx(
            "rounded-md px-2.5 py-1 font-medium",
            active === t.id
              ? "bg-white text-slate-900 shadow-sm"
              : "text-slate-600 hover:text-slate-900"
          )}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}