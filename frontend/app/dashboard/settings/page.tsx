import { cookies } from "next/headers";
import { getServerSession } from "@/lib/auth/session";
import Link from "next/link";
import { IntegrationsForm } from "@/components/settings/IntegrationsForm";
import { PublicBookingLink } from "@/components/settings/PublicBookingLink";
import { WorkspaceStatusCard } from "@/components/settings/WorkspaceStatusCard";
import { StaffManagement } from "@/components/settings/StaffManagement";
import { InventoryManagement } from "@/components/settings/InventoryManagement";
import { FormManagement } from "@/components/settings/FormManagement";

export default function SettingsPage() {
  const user = getServerSession();
  if (!user) return null;

  const cookieStore = cookies();
  const token = cookieStore.get("auth_token")?.value ?? "";

  const sections = [
    {
      id: "integrations",
      title: "Email & SMS",
      description:
        "Connect at least one channel. Email for confirmations and alerts; SMS for reminders. Failures are logged and visible.",
      integrations: true,
    },
    {
      id: "contact-form",
      title: "Contact form",
      description:
        "Public form fields: name, email or phone, optional message. Submissions create a Contact and start a Conversation with a welcome message.",
      placeholder: "Set form fields and welcome message. API coming soon.",
    },
    {
      id: "forms",
      title: "Forms (post-booking)",
      description:
        "Control form availability after submission. Keep forms active for ongoing conversations or deactivate when complete.",
      forms: true,
    },
    {
      id: "staff",
      title: "Staff & permissions",
      description:
        "Invite staff and assign permissions: Inbox, Bookings, Forms, Inventory visibility. Staff cannot change configuration or automation.",
      staff: true,
    },
    {
      id: "inventory",
      title: "Inventory & Resources",
      description:
        "Manage items and resources used per booking. Set quantities and reorder thresholds for automated alerts and usage forecasting.",
      inventory: true,
    },
    {
      id: "activate",
      title: "Activate workspace",
      description:
        "We verify: communication channel connected, at least one booking type, availability defined. Then forms and booking links go live.",
      activate: true,
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Workspace settings</h1>
        <p className="mt-1 text-sm text-slate-600">
          Configure integrations, contact form, forms, staff, and activate your workspace.
        </p>
        <div className="mt-4">
          <PublicBookingLink workspaceId={user.workspace_id} />
        </div>
      </div>

      {sections.map((s) => (
        <section key={s.id} id={s.id} className="card p-4 scroll-mt-6">
          <h2 className="text-lg font-medium text-slate-900">{s.title}</h2>
          <p className="mt-1 text-sm text-slate-600">{s.description}</p>
          {"integrations" in s && s.integrations ? (
            <div className="mt-3">
              <IntegrationsForm workspaceId={user.workspace_id} token={token} />
            </div>
          ) : "activate" in s && s.activate ? (
            <div className="mt-3">
              <WorkspaceStatusCard workspaceId={user.workspace_id} token={token} />
            </div>
          ) : "forms" in s && s.forms ? (
            <div className="mt-3">
              <FormManagement workspaceId={user.workspace_id} token={token} />
            </div>
          ) : "staff" in s && s.staff ? (
            <div className="mt-3">
              <StaffManagement workspaceId={user.workspace_id} token={token} />
            </div>
          ) : "inventory" in s && s.inventory ? (
            <div className="mt-3">
              <InventoryManagement workspaceId={user.workspace_id} token={token} />
            </div>
          ) : (
            <div className="mt-3 rounded-md border border-dashed border-slate-200 bg-slate-50/50 px-4 py-3 text-sm text-slate-500">
              {s.placeholder}
            </div>
          )}
        </section>
      ))}
    </div>
  );
}
