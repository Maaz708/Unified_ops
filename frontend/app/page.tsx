export default function MarketingPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4">
      <div className="max-w-3xl text-center">
        <h1 className="text-4xl font-semibold tracking-tight text-slate-900 sm:text-5xl">
          Unified Operations Platform
        </h1>
        <p className="mt-4 text-lg text-slate-600">
          One workspace for bookings, conversations, inventory, and automated workflows.
        </p>
        <div className="mt-8 flex justify-center gap-4">
          <a
            href="/onboarding"
            className="rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-brand-700"
          >
            Get started
          </a>
          <a
            href="/login"
            className="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-100"
          >
            Log in
          </a>
        </div>
      </div>
    </main>
  );
}
