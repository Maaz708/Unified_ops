import { request } from "./client";

export function apiAuthLogin(body: { email: string; password: string }) {
  // In production you would set HttpOnly cookie via backend; here we just call it.
  return request(`/auth/login`, { method: "POST", body });
}