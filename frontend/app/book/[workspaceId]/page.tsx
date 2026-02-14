"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  listPublicBookingTypes,
  getPublicAvailability,
  getPublicAvailabilityRange,
  createPublicBooking,
  type PublicBookingType,
  type PublicAvailabilitySlot,
} from "@/lib/api/publicBooking";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";

type Step = "type" | "date" | "slot" | "details" | "done";

function formatSlotTime(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
  } catch {
    return iso;
  }
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      weekday: "short",
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}

function getMonthRange(year: number, month: number): { from: string; to: string } {
  const from = `${year}-${String(month).padStart(2, "0")}-01`;
  const lastDay = new Date(year, month, 0).getDate();
  const to = `${year}-${String(month).padStart(2, "0")}-${String(lastDay).padStart(2, "0")}`;
  return { from, to };
}

function todayYYYYMMDD(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function monthCalendarDays(year: number, month: number): (number | null)[] {
  const first = new Date(year, month - 1, 1);
  const last = new Date(year, month, 0).getDate();
  const startWeekday = first.getDay();
  const pad: null[] = Array(startWeekday).fill(null);
  const days = Array.from({ length: last }, (_, i) => i + 1);
  return [...pad, ...days];
}

export default function PublicBookingPage() {
  const params = useParams();
  const workspaceId = (params?.workspaceId ?? "") as string;

  const [step, setStep] = useState<Step>("type");
  const [types, setTypes] = useState<PublicBookingType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedType, setSelectedType] = useState<PublicBookingType | null>(null);
  const [calendarYear, setCalendarYear] = useState(() => new Date().getFullYear());
  const [calendarMonth, setCalendarMonth] = useState(() => new Date().getMonth() + 1);
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [loadingCalendar, setLoadingCalendar] = useState(false);
  const [selectedDate, setSelectedDate] = useState("");
  const [slots, setSlots] = useState<PublicAvailabilitySlot[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<PublicAvailabilitySlot | null>(null);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [submitLoading, setSubmitLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadTypes = useCallback(() => {
    setLoading(true);
    setError(null);
    listPublicBookingTypes(workspaceId)
      .then(setTypes)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [workspaceId]);

  useEffect(() => {
    loadTypes();
  }, [loadTypes]);

  const handleSelectType = (t: PublicBookingType) => {
    setSelectedType(t);
    setSelectedDate("");
    setSlots([]);
    setSelectedSlot(null);
    setCalendarYear(new Date().getFullYear());
    setCalendarMonth(new Date().getMonth() + 1);
    setStep("date");
  };

  useEffect(() => {
    if (step !== "date" || !selectedType) return;
    const { from, to } = getMonthRange(calendarYear, calendarMonth);
    setLoadingCalendar(true);
    getPublicAvailabilityRange(workspaceId, selectedType.slug, from, to)
      .then(setAvailableDates)
      .catch((e) => setError(e.message))
      .finally(() => setLoadingCalendar(false));
  }, [step, selectedType, workspaceId, calendarYear, calendarMonth]);

  const availableSet = new Set(availableDates);
  const today = todayYYYYMMDD();

  const handleSelectDay = (dateStr: string) => {
    if (dateStr < today || !availableSet.has(dateStr)) return;
    setSelectedDate(dateStr);
    setSelectedSlot(null);
    setLoading(true);
    getPublicAvailability(workspaceId, selectedType!.slug, dateStr)
      .then(setSlots)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  const goPrevMonth = () => {
    if (calendarMonth === 1) {
      setCalendarMonth(12);
      setCalendarYear((y) => y - 1);
    } else {
      setCalendarMonth((m) => m - 1);
    }
  };

  const goNextMonth = () => {
    if (calendarMonth === 12) {
      setCalendarMonth(1);
      setCalendarYear((y) => y + 1);
    } else {
      setCalendarMonth((m) => m + 1);
    }
  };

  const availableSlots = slots.filter((s) => s.is_available);

  const handleSubmitBooking = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedType || !selectedSlot) return;
    if (!email?.trim() && !phone?.trim()) {
      setError("Please enter email or phone.");
      return;
    }
    setSubmitLoading(true);
    setError(null);
    try {
      const booking = await createPublicBooking(workspaceId, {
        booking_type_slug: selectedType.slug,
        start_at: selectedSlot.slot_start,
        end_at: selectedSlot.slot_end,
        full_name: fullName.trim(),
        email: email.trim() || undefined,
        phone: phone.trim() || undefined,
      });

      // Fire-and-forget confirmation via Next.js API route (email + SMS),
      // using your configured SMTP and Twilio credentials.
      try {
        await fetch("/api/send-confirmation", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            bookingId: booking.booking.id,
            contactName: fullName.trim(),
            email: email.trim() || undefined,
            phoneNumber: phone.trim() || undefined,
            startAt: selectedSlot.slot_start,
          }),
        });
      } catch {
        // Don't block the booking on notification errors
      }

      // If this booking type has a form, send form link email
      const contactEmail = email?.trim();
      if (contactEmail) {
        try {
          const formLinkRes = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL?.replace(/\/?$/, "") || "http://localhost:8000/api/v1"}/public/${workspaceId}/bookings/${booking.booking.id}/form-link`
          );
          if (formLinkRes.ok) {
            const formLink = await formLinkRes.json();
            if (formLink?.form_template_id) {
              await fetch("/api/send-form-link", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                workspaceId,
                bookingId: booking.booking.id,
                contactId: booking.booking.contact_id,
                contactName: fullName.trim(),
                contactEmail,
                formTemplateId: formLink.form_template_id,
              }),
            });
            }
          }
        } catch {
          // Don't block on form link errors
        }
      }

      setSuccessMessage("Booking confirmed. Check your email for details.");
      setStep("done");
    } catch (e: any) {
      setError(e.message ?? "Booking failed.");
    } finally {
      setSubmitLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-8">
      <div className="mx-auto max-w-lg">
        <h1 className="text-xl font-semibold text-slate-900">Book a service</h1>
        <p className="mt-1 text-sm text-slate-600">
          Choose a service, pick a time, and enter your details. No account needed.
        </p>

        {error && (
          <div className="mt-4 rounded-md bg-red-50 px-4 py-2 text-sm text-red-800">
            {error}
          </div>
        )}

        {step === "type" && (
          <div className="mt-6">
            {loading ? (
              <p className="text-sm text-slate-500">Loading options…</p>
            ) : types.length === 0 ? (
              <p className="text-sm text-slate-500">
                No booking types available for this workspace, or the link may be incorrect.
              </p>
            ) : (
              <ul className="space-y-2">
                {types.map((t) => (
                  <li key={t.id}>
                    <button
                      type="button"
                      onClick={() => handleSelectType(t)}
                      className="card w-full p-4 text-left hover:border-brand-300 hover:bg-brand-50/50"
                    >
                      <span className="font-medium text-slate-900">{t.name}</span>
                      {t.description && (
                        <p className="mt-1 text-sm text-slate-600">{t.description}</p>
                      )}
                      <p className="mt-1 text-xs text-slate-500">{t.duration_minutes} min</p>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        {step === "date" && selectedType && (
          <div className="mt-6 space-y-4">
            <p className="text-sm text-slate-600">
              Selected: <span className="font-medium text-slate-900">{selectedType.name}</span>
            </p>
            <p className="text-xs text-slate-500">
              Choose a date with available slots (highlighted). Then pick a time below.
            </p>

            <div className="card p-4">
              <div className="mb-3 flex items-center justify-between">
                <button
                  type="button"
                  onClick={goPrevMonth}
                  className="rounded p-1.5 text-slate-600 hover:bg-slate-100"
                  aria-label="Previous month"
                >
                  ←
                </button>
                <span className="text-sm font-semibold text-slate-800">
                  {new Date(calendarYear, calendarMonth - 1).toLocaleString(undefined, {
                    month: "long",
                    year: "numeric",
                  })}
                </span>
                <button
                  type="button"
                  onClick={goNextMonth}
                  className="rounded p-1.5 text-slate-600 hover:bg-slate-100"
                  aria-label="Next month"
                >
                  →
                </button>
              </div>
              {loadingCalendar ? (
                <p className="py-4 text-center text-sm text-slate-500">Loading availability…</p>
              ) : (
                <>
                  <div className="grid grid-cols-7 gap-0.5 text-center text-xs font-medium text-slate-500">
                    {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((d) => (
                      <div key={d}>{d}</div>
                    ))}
                  </div>
                  <div className="mt-1 grid grid-cols-7 gap-0.5">
                    {monthCalendarDays(calendarYear, calendarMonth).map((day, i) => {
                      if (day === null) return <div key={`e-${i}`} />;
                      const dateStr = `${calendarYear}-${String(calendarMonth).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
                      const isAvailable = availableSet.has(dateStr);
                      const isPast = dateStr < today;
                      const isSelected = selectedDate === dateStr;
                      const clickable = isAvailable && !isPast;
                      return (
                        <button
                          key={dateStr}
                          type="button"
                          disabled={!clickable}
                          onClick={() => clickable && handleSelectDay(dateStr)}
                          className={`rounded p-2 text-sm ${
                            !clickable
                              ? "cursor-default text-slate-300"
                              : isSelected
                                ? "bg-brand-600 text-white"
                                : "bg-slate-100 text-slate-800 hover:bg-brand-100 hover:text-brand-800"
                          }`}
                        >
                          {day}
                        </button>
                      );
                    })}
                  </div>
                </>
              )}
            </div>

            {selectedDate && (
              <div className="space-y-2">
                <p className="text-sm font-medium text-slate-700">
                  Times on {formatDate(selectedDate + "T12:00:00")}
                </p>
                {loading ? (
                  <p className="text-sm text-slate-500">Loading times…</p>
                ) : availableSlots.length === 0 ? (
                  <p className="text-sm text-slate-500">No available slots on this date.</p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {availableSlots.map((s) => (
                      <button
                        key={`${s.slot_start}-${s.slot_end}`}
                        type="button"
                        onClick={() => {
                          setSelectedSlot(s);
                          setStep("details");
                        }}
                        className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                      >
                        {formatSlotTime(s.slot_start)}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            <Button variant="outline" onClick={() => setStep("type")}>
              Back
            </Button>
          </div>
        )}

        {step === "details" && selectedType && selectedSlot && (
          <div className="mt-6 space-y-4">
            <p className="text-sm text-slate-600">
              {selectedType.name} • {formatDate(selectedSlot.slot_start)} at{" "}
              {formatSlotTime(selectedSlot.slot_start)}
            </p>
            <form onSubmit={handleSubmitBooking} className="space-y-4">
              <Input
                label="Full name"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
              <Input
                label="Email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Or use phone below"
              />
              <Input
                label="Phone"
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="Or use email above"
              />
              <p className="text-xs text-slate-500">Provide at least one of email or phone.</p>
              <div className="flex gap-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setStep("date");
                    setSelectedSlot(null);
                  }}
                >
                  Back
                </Button>
                <Button type="submit" disabled={submitLoading}>
                  {submitLoading ? "Booking…" : "Confirm booking"}
                </Button>
              </div>
            </form>
          </div>
        )}

        {step === "done" && (
          <div className="card mt-6 p-6 text-center">
            <p className="font-medium text-slate-900">{successMessage}</p>
            <p className="mt-2 text-sm text-slate-600">
              You can close this page. We&apos;ll send a confirmation to your email.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
