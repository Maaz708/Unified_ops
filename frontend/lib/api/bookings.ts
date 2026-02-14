import { request } from "./client";

export function updateBookingStatus(
  workspaceId: string,
  bookingId: string,
  status: "confirmed" | "completed" | "no_show" | "cancelled",
  token: string
): Promise<{ id: string; status: string }> {
  return request<{ id: string; status: string }>(
    `/workspaces/${workspaceId}/bookings/${bookingId}/status`,
    { method: "PATCH", body: { status }, token }
  );
}
