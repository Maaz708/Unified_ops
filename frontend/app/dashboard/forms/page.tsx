import { cookies } from "next/headers";
import { getServerSession } from "@/lib/auth/session";
import { redirect } from "next/navigation";
import { FormsPageContent } from "@/components/dashboard/FormsPageContent";

export default async function FormsPage() {
  const user = getServerSession();
  if (!user) {
    redirect("/login");
    return null;
  }

  const cookieStore = cookies();
  const token = cookieStore.get("auth_token")?.value ?? "";

  return (
    <FormsPageContent workspaceId={user.workspace_id} token={token} />
  );
}
