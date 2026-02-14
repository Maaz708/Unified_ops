const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/?$/, "") || "http://localhost:8000/api/v1";

export interface PublicBookingType {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  duration_minutes: number;
}

export interface PublicAvailabilitySlot {
  slot_start: string;
  slot_end: string;
  staff_name: string | null;
  is_available: boolean;
}

export interface PublicBookingCreateRequest {
  booking_type_slug: string;
  start_at: string;
  end_at: string;
  full_name: string;
  email?: string | null;
  phone?: string | null;
}

export interface PublicBookingResponse {
  booking: {
    id: string;
    status: string;
    start_at: string;
    end_at: string;
    contact_id: string;
    conversation_id: string | null;
    booking_type_id: string;
  };
  message_channel: string | null;
}

export async function listPublicBookingTypes(workspaceId: string): Promise<PublicBookingType[]> {
  const res = await fetch(`${API_URL}/public/${workspaceId}/booking-types`, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text().catch(() => "Failed to load booking types"));
  return res.json();
}

export async function getPublicAvailability(
  workspaceId: string,
  slug: string,
  day: string
): Promise<PublicAvailabilitySlot[]> {
  const res = await fetch(
    `${API_URL}/public/${workspaceId}/booking-types/${encodeURIComponent(slug)}/availability?day=${day}`,
    { cache: "no-store" }
  );
  if (!res.ok) throw new Error(await res.text().catch(() => "Failed to load availability"));
  return res.json();
}

/**
 * Returns dates in [fromDate, toDate] that have at least one available slot.
 * Use for month calendar: only these dates are clickable.
 */
export async function getPublicAvailabilityRange(
  workspaceId: string,
  slug: string,
  fromDate: string,
  toDate: string
): Promise<string[]> {
  const res = await fetch(
    `${API_URL}/public/${workspaceId}/booking-types/${encodeURIComponent(slug)}/availability-range?from_date=${fromDate}&to_date=${toDate}`,
    { cache: "no-store" }
  );
  if (!res.ok) throw new Error(await res.text().catch(() => "Failed to load availability"));
  return res.json();
}

export async function createPublicBooking(
  workspaceId: string,
  body: PublicBookingCreateRequest
): Promise<PublicBookingResponse> {
  const res = await fetch(`${API_URL}/public/${workspaceId}/bookings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text().catch(() => "Booking failed"));
  return res.json();
}
