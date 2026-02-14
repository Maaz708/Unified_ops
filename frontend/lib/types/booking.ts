export type BookingStatus = "pending" | "confirmed" | "cancelled" | "completed" | "no_show";

export interface BookingType {
  id: string;
  name: string;
  slug: string;
  description?: string;
  duration_minutes: number;
}

export type BookingCard = {
  id: string;
  contact_name?: string;
  start_at: string;
  end_at: string;
  status: BookingStatus;
  booking_type_name?: string;
  contact_id?: string;
  primary_email?: string | null;
  primary_phone?: string | null;
  /** @deprecated use primary_email */
  email?: string;
  /** @deprecated use primary_phone */
  phone_number?: string;
}