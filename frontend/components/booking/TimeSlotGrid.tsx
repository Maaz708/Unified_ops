"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";

interface Slot {
  slot_start: string;
  slot_end: string;
  staff_name?: string;
  is_available: boolean;
}

export function TimeSlotGrid({ workspaceId }: { workspaceId: string }) {
  const [slots, setSlots] = useState<Slot[]>([]);

  // Stub; in a full implementation you’d fetch for selected booking type + date.
  useEffect(() => {
    setSlots([]);
  }, [workspaceId]);

  if (!slots.length) {
    return <p className="text-sm text-slate-500">Select a date and service to see availability.</p>;
  }

  return (
    <div className="grid grid-cols-2 gap-2">
      {slots.map((s) => (
        <Button
          key={s.slot_start}
          variant={s.is_available ? "outline" : "ghost"}
          disabled={!s.is_available}
        >
          {new Date(s.slot_start).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </Button>
      ))}
    </div>
  );
}