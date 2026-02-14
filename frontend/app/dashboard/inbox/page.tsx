import { cookies } from "next/headers";
import { getServerSession } from "@/lib/auth/session";
import { redirect } from "next/navigation";
import { InboxPageContent } from "@/components/inbox/InboxPageContent";

export default async function InboxPage() {
  const user = getServerSession();
  if (!user) {
    redirect("/login");
    return null;
  }
  const token = (await cookies()).get("auth_token")?.value ?? "";
  return <InboxPageContent token={token} />;
}
