"use client";

import clsx from "clsx";
import type { ButtonHTMLAttributes, ReactNode } from "react";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: "primary" | "outline" | "ghost";
}

export function Button({ children, className, variant = "primary", ...rest }: Props) {
  const base =
    "inline-flex items-center justify-center rounded-lg px-3 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2";
  const styles = {
    primary: "bg-brand-600 text-white hover:bg-brand-700 focus:ring-brand-500",
    outline:
      "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 focus:ring-slate-400",
    ghost: "text-slate-700 hover:bg-slate-100 focus:ring-slate-400"
  };
  return (
    <button className={clsx(base, styles[variant], className)} {...rest}>
      {children}
    </button>
  );
}