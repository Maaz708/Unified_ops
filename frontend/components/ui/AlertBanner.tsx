export function AlertBanner({ message }: { message: string }) {
    return (
      <div className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-800">
        {message}
      </div>
    );
  }