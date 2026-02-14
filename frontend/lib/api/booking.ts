import { request } from "./client";
import type { BookingType } from "@/lib/types/booking";

export function getPublicBookingTypes(workspaceId: string) {
  return request<BookingType[]>(`/public/${workspaceId}/booking-types`);
}

export function createPublicBooking(input: {
  workspaceId: string;
  booking_type_slug: string;
  start_at: string;
  end_at: string;
  full_name: string;
  email?: string;
  phone?: string;
}) {
  const { workspaceId, ...payload } = input;
  return request(`/public/${workspaceId}/bookings`, {
    method: "POST",
    body: payload
  });
}