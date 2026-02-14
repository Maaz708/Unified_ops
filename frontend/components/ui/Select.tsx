"use client";

import type { SelectHTMLAttributes, ReactNode } from "react";

interface Props extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  children: ReactNode;
}

export function Select({ label, children, ...rest }: Props) {
  return (
    <label className="block text-sm">
      {label && <span className="mb-1 block text-slate-700">{label}</span>}
      <select
        className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
        {...rest}
      >
        {children}
      </select>
    </label>
  );
}