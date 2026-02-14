"use client";

import type { SessionUser } from "@/lib/auth/session";

function logout() {
  document.cookie = "auth_token=; path=/; max-age=0";
  window.location.href = "/login";
}

export function Topbar({ user, onMenuClick }: { user: SessionUser; onMenuClick?: () => void }) {
  return (
    <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white/80 px-4 backdrop-blur-sm">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onMenuClick}
          className="lg:hidden flex h-10 w-10 items-center justify-center rounded-lg text-slate-600 hover:bg-slate-100"
          aria-label="Open menu"
        >
          <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <span className="text-sm font-medium text-slate-700">
          Workspace <span className="font-semibold">{user.workspace_id}</span>
        </span>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-sm text-slate-600">{user.email}</span>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
          {user.role}
        </span>
        <button
          type="button"
          onClick={logout}
          className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          Log out
        </button>
      </div>
    </header>
  );
}