"use client";

import { useState } from "react";
import type { BookingType } from "@/lib/types/booking";
import { Select } from "@/components/ui/Select";

export function BookingTypeSelector({ bookingTypes }: { bookingTypes: BookingType[] }) {
  const [active, setActive] = useState(bookingTypes[0]?.slug);

  // In a full implementation you'd lift this state up and pass to TimeSlotGrid/BookingForm
  return (
    <div className="space-y-2">
      <h2 className="text-sm font-semibold text-slate-700">Choose a service</h2>
      <Select value={active} onChange={(e) => setActive(e.target.value)}>
        {bookingTypes.map((bt) => (
          <option key={bt.id} value={bt.slug}>
            {bt.name}
          </option>
        ))}
      </Select>
    </div>
  );
}