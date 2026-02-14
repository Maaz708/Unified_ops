import type { ReactNode } from "react";
import { redirect } from "next/navigation";

import { getServerSession } from "@/lib/auth/session";
import { AppShell } from "@/components/layout/AppShell";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const user = getServerSession();
  if (!user) {
    redirect("/login");
  }

  return <AppShell user={user}>{children}</AppShell>;
}
