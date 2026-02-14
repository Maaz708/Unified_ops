'use client';

import { useRouter } from "next/navigation";
import type { BookingCard } from "@/lib/types/booking";
import { Table } from "@/components/ui/Table";
import { useState } from "react";
import { updateBookingStatus, sendBookingConfirmation } from "@/lib/api/bookings";

const API_URL = process.env.NEXT_PUBLIC_API_URL?.replace(/\/?$/, "") || "http://localhost:8000/api/v1";

export function BookingList({
  bookings,
  workspaceId,
  token,
  showHistory = false,
}: {
  bookings: BookingCard[];
  workspaceId?: string;
  token?: string;
  /** When true, rows are not clickable for sending confirmation (used for history list). */
  showHistory?: boolean;
}) {
  const router = useRouter();
  const [selectedBookingId, setSelectedBookingId] = useState<string | null>(null);

  async function sendConfirmationMessage(booking: BookingCard) {
    const email = booking.primary_email ?? booking.email ?? undefined;
    const phoneNumber = booking.primary_phone ?? booking.phone_number ?? undefined;
    const contactName = booking.contact_name?.trim() || "Customer";

    if (!email && !phoneNumber) {
      alert("No email or phone on file for this contact. Add contact details in the contact record to send confirmation.");
      return;
    }

    try {
      if (!token) {
        throw new Error("Authentication required");
      }
      
      await sendBookingConfirmation(
        booking.id,
        contactName,
        email || "",
        booking.start_at,
        token
      );

      // Mark as confirmed when owner/staff sends confirmation (so it shows correctly in dashboard)
      if (workspaceId && token && (booking.status === "pending" || booking.status === "confirmed")) {
        try {
          await updateBookingStatus(workspaceId, booking.id, "confirmed", token);
        } catch {
          // Non-fatal
        }
      }

      // If workspace and contact email exist, send form link if this booking type has a form
      if (workspaceId && email && booking.contact_id) {
        try {
          const formLinkRes = await fetch(
            `${API_URL}/public/${workspaceId}/bookings/${booking.id}/form-link`
          );
          if (formLinkRes.ok) {
            const formLink = await formLinkRes.json();
            if (formLink?.form_template_id) {
              await fetch("/api/send-form-link", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                workspaceId,
                bookingId: booking.id,
                contactId: booking.contact_id,
                contactName,
                contactEmail: email,
                formTemplateId: formLink.form_template_id,
              }),
            });
            }
          }
        } catch {
          // Form link is best-effort; don't fail the flow
        }
      }

      alert(`Confirmation sent to ${contactName}.${workspaceId ? " Form link sent if applicable." : ""}`);
      router.refresh();
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : "An unknown error occurred.";
      alert(`Error sending confirmation: ${errorMessage}`);
    }
  }

  if (!bookings.length) {
    return (
      <p className="text-sm text-slate-500">
        {showHistory ? "No past bookings in the last 30 days." : "No bookings for today."}
      </p>
    );
  }

  return (
    <Table>
      <thead className="bg-slate-50">
        <tr>
          <th className="px-4 py-2 text-left text-xs font-medium text-slate-500">Time</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-slate-500">Contact</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-slate-500">Type</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-slate-500">Status</th>
          {!showHistory && workspaceId && token && (
            <th className="px-4 py-2 text-left text-xs font-medium text-slate-500">Actions</th>
          )}
        </tr>
      </thead>
      <tbody className="divide-y divide-slate-100 bg-white text-sm">
        {bookings.map((b) => (
          <tr
            key={b.id}
            onClick={
              showHistory
                ? undefined
                : () => {
                    setSelectedBookingId(b.id);
                    sendConfirmationMessage(b);
                  }
            }
            className={
              showHistory
                ? ""
                : selectedBookingId === b.id
                  ? "bg-blue-100 cursor-pointer"
                  : "cursor-pointer"
            }
          >
            <td className="px-4 py-2 text-slate-700" suppressHydrationWarning>
              {new Date(b.start_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </td>
            <td className="px-4 py-2 text-slate-800">{b.contact_name || "Unknown"}</td>
            <td className="px-4 py-2 text-slate-700">{b.booking_type_name || "-"}</td>
            <td className="px-4 py-2 text-xs uppercase text-slate-500">{b.status}</td>
            {!showHistory && workspaceId && token && (
              <td className="px-4 py-2" onClick={(e) => e.stopPropagation()}>
                {b.status !== "completed" && b.status !== "no_show" && (
                  <span className="flex gap-1 flex-wrap">
                    <button
                      type="button"
                      className="text-xs font-medium text-green-700 hover:underline"
                      onClick={async () => {
                        try {
                          await updateBookingStatus(workspaceId!, b.id, "completed", token);
                          router.refresh();
                        } catch {
                          alert("Failed to update status");
                        }
                      }}
                    >
                      Mark completed
                    </button>
                    <button
                      type="button"
                      className="text-xs font-medium text-amber-700 hover:underline"
                      onClick={async () => {
                        try {
                          await updateBookingStatus(workspaceId!, b.id, "no_show", token);
                          router.refresh();
                        } catch {
                          alert("Failed to update status");
                        }
                      }}
                    >
                      No-show
                    </button>
                  </span>
                )}
              </td>
            )}
          </tr>
        ))}
      </tbody>
    </Table>
  );
}