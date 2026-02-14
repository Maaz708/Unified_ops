"use client";

import { useEffect, useState } from "react";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import {
  listAvailabilitySlots,
  createAvailabilitySlot,
  deleteAvailabilitySlot,
  type AvailabilitySlotOut,
} from "@/lib/api/workspace";
import { listPublicBookingTypes, type PublicBookingType } from "@/lib/api/publicBooking";

function formatDateTime(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function AvailabilityManager({
  workspaceId,
  token,
}: {
  workspaceId: string;
  token: string;
}) {
  const [slots, setSlots] = useState<AvailabilitySlotOut[]>([]);
  const [bookingTypes, setBookingTypes] = useState<PublicBookingType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);

  const [bookingTypeSlug, setBookingTypeSlug] = useState("");
  const [date, setDate] = useState("");
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("17:00");

  useEffect(() => {
    if (!token) return;
    Promise.all([
      listAvailabilitySlots(workspaceId, token),
      listPublicBookingTypes(workspaceId),
    ])
      .then(([s, bt]) => {
        setSlots(s);
        setBookingTypes(bt);
        if (bt.length > 0) setBookingTypeSlug(bt[0].slug);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [workspaceId, token]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!bookingTypeSlug || !date || !startTime || !endTime) {
      setError("Please fill all fields.");
      return;
    }
    // Create dates in local timezone, then convert to ISO (UTC) for backend
    const start = new Date(`${date}T${startTime}:00`);
    const end = new Date(`${date}T${endTime}:00`);
    if (end <= start) {
      setError("End time must be after start time.");
      return;
    }
    // Ensure we're sending UTC ISO strings
    const startISO = start.toISOString();
    const endISO = end.toISOString();
    setSaving(true);
    setError(null);
    try {
      const newSlot = await createAvailabilitySlot(
        workspaceId,
        {
          booking_type_slug: bookingTypeSlug,
          start_at: startISO,
          end_at: endISO,
        },
        token
      );
      setSlots([...slots, newSlot].sort((a, b) => a.start_at.localeCompare(b.start_at)));
      setShowForm(false);
      setDate("");
      setStartTime("09:00");
      setEndTime("17:00");
    } catch (e: any) {
      setError(e.message ?? "Failed to add slot");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (slotId: string) => {
    if (!confirm("Delete this availability slot?")) return;
    try {
      await deleteAvailabilitySlot(workspaceId, slotId, token);
      setSlots(slots.filter((s) => s.id !== slotId));
    } catch (e: any) {
      setError(e.message ?? "Failed to delete");
    }
  };

  if (!token) {
    return <p className="text-sm text-slate-500">Sign in to manage availability.</p>;
  }

  if (loading) {
    return <p className="text-sm text-slate-500">Loading availability…</p>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-700">Availability slots</h3>
        <Button variant="outline" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "Add slot"}
        </Button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {showForm && (
        <form onSubmit={handleAdd} className="card p-4 space-y-3">
          <Select
            label="Booking type"
            value={bookingTypeSlug}
            onChange={(e) => setBookingTypeSlug(e.target.value)}
            required
          >
            {bookingTypes.map((bt) => (
              <option key={bt.slug} value={bt.slug}>
                {bt.name}
              </option>
            ))}
          </Select>
          <Input
            label="Date"
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            required
            min={new Date().toISOString().split("T")[0]}
          />
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Start time"
              type="time"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              required
            />
            <Input
              label="End time"
              type="time"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              required
            />
          </div>
          <Button type="submit" disabled={saving}>
            {saving ? "Adding…" : "Add availability"}
          </Button>
        </form>
      )}

      {slots.length === 0 ? (
        <p className="text-sm text-slate-500">No availability slots. Add one above to enable bookings.</p>
      ) : (
        <ul className="space-y-2">
          {slots.map((s) => (
            <li key={s.id} className="card p-3 flex items-center justify-between">
              <div>
                <span className="font-medium text-slate-900">{s.booking_type_name}</span>
                <p className="text-sm text-slate-600">
                  {formatDateTime(s.start_at)} – {formatDateTime(s.end_at)}
                </p>
                {s.staff_name && <p className="text-xs text-slate-500">Staff: {s.staff_name}</p>}
              </div>
              <button
                type="button"
                onClick={() => handleDelete(s.id)}
                className="text-xs text-red-600 hover:underline"
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
