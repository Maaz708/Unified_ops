import { notFound } from "next/navigation";
import { BookingTypeSelector } from "@/components/booking/BookingTypeSelector";
import { TimeSlotGrid } from "@/components/booking/TimeSlotGrid";
import { BookingForm } from "@/components/booking/BookingForm";
import { getPublicBookingTypes } from "@/lib/api/booking";

interface Props {
  params: { workspaceId: string };
}

export default async function PublicBookingPage({ params }: Props) {
  const bookingTypes = await getPublicBookingTypes(params.workspaceId).catch(() => null);
  if (!bookingTypes) notFound();

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
        <div className="text-lg font-semibold">Unified Ops – Booking</div>
      </header>
      <main className="mx-auto grid max-w-5xl gap-6 px-4 pb-10 md:grid-cols-[2fr,1.5fr]">
        <div className="card p-4 space-y-4">
          <BookingTypeSelector bookingTypes={bookingTypes} />
          <TimeSlotGrid workspaceId={params.workspaceId} />
        </div>
        <div className="card p-4">
          <BookingForm workspaceId={params.workspaceId} />
        </div>
      </main>
    </div>
  );
}