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

export function sendBookingConfirmation(
  bookingId: string,
  contactName: string,
  email: string,
  startAt: string,
  token: string
): Promise<{ message: string }> {
  return request<{ message: string }>(
    "/bookings/send-confirmation",
    { 
      method: "POST", 
      body: { 
        booking_id: bookingId,
        contact_name: contactName,
        email: email,
        start_at: startAt
      }, 
      token 
    }
  );
}
