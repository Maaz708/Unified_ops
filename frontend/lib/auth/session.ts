import { cookies } from "next/headers";
import { jwtDecode } from "jwt-decode";

export type UserRole = "owner" | "staff";

export interface SessionUser {
  id: string;
  email: string;
  role: UserRole;
  workspace_id: string;
}

export function getServerSession(): SessionUser | null {
  const cookieStore = cookies();
  const token = cookieStore.get("auth_token")?.value;
  if (!token) return null;
  try {
    const decoded = jwtDecode<any>(token);
    return {
      id: decoded.sub,
      email: decoded.email,
      role: decoded.role,
      workspace_id: decoded.workspace_id,
    };
  } catch {
    return null;
  }
}