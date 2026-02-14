"use client";

interface MessageStub {
  id: string;
  direction: "inbound" | "outbound";
  body_text: string;
  created_at: string;
}

export function MessageThread({ messages }: { messages: MessageStub[] }) {
  if (!messages.length) {
    return <p className="text-sm text-slate-500">No messages yet.</p>;
  }
  return (
    <div className="space-y-3 text-sm">
      {messages.map((m) => (
        <div key={m.id} className="flex flex-col">
          <div
            className={`max-w-lg rounded-lg px-3 py-2 ${
              m.direction === "outbound"
                ? "self-end bg-brand-600 text-white"
                : "self-start bg-slate-100 text-slate-800"
            }`}
          >
            {m.body_text}
          </div>
          <span className="mt-1 text-xs text-slate-400">
            {new Date(m.created_at).toLocaleString()}
          </span>
        </div>
      ))}
    </div>
  );
}