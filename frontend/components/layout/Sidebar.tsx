"use client";

import Link from "next/link";
import clsx from "clsx";
import type { UserRole } from "@/lib/auth/session";

const baseItems = [
  { href: "/dashboard", label: "Overview" },
  { href: "/dashboard/inbox", label: "Inbox" },
  { href: "/dashboard/bookings", label: "Bookings" },
  { href: "/dashboard/forms", label: "Forms" },
  { href: "/dashboard/inventory", label: "Inventory" },
  { href: "/dashboard/analytics", label: "Analytics" },
];

const ownerOnly = [
  { href: "/dashboard/settings", label: "Settings" },
];

export function Sidebar({
  role,
  pathname,
  mobileOpen = false,
  onMobileClose,
}: {
  role: UserRole;
  pathname: string;
  mobileOpen?: boolean;
  onMobileClose?: () => void;
}) {
  const items = role === "owner" ? [...baseItems, ...ownerOnly] : baseItems;

  const navContent = (
    <>
      <div className="flex h-16 items-center justify-between px-6">
        <span className="text-lg font-semibold text-slate-900">Unified Ops</span>
        {onMobileClose && (
          <button
            type="button"
            onClick={onMobileClose}
            className="lg:hidden flex h-10 w-10 items-center justify-center rounded-lg text-slate-600 hover:bg-slate-100"
            aria-label="Close menu"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
      <nav className="space-y-1 px-3 pb-4">
        {items.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            onClick={onMobileClose}
            className={clsx(
              "flex items-center rounded-lg px-3 py-2 text-sm font-medium",
              pathname === item.href
                ? "bg-brand-50 text-brand-700"
                : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
            )}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </>
  );

  return (
    <>
      {/* Backdrop for mobile */}
      {mobileOpen && (
        <button
          type="button"
          onClick={onMobileClose}
          className="fixed inset-0 z-40 bg-slate-900/50 lg:hidden"
          aria-label="Close menu"
        />
      )}
      {/* Desktop: always visible from lg up */}
      <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white/90 backdrop-blur-sm lg:block">
        <div className="flex h-16 items-center px-6 text-lg font-semibold text-slate-900">
          Unified Ops
        </div>
        <nav className="space-y-1 px-3 pb-4">
          {items.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "flex items-center rounded-lg px-3 py-2 text-sm font-medium",
                pathname === item.href
                  ? "bg-brand-50 text-brand-700"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>
      {/* Mobile: slide-out panel */}
      <aside
        className={clsx(
          "fixed inset-y-0 left-0 z-50 w-64 border-r border-slate-200 bg-white shadow-xl transition-transform duration-200 ease-out lg:hidden",
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {navContent}
      </aside>
    </>
  );
}