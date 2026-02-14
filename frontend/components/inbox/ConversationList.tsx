"use client";

interface ConversationStub {
  id: string;
  contact_name: string;
  last_message_at: string;
}

export function ConversationList({
  conversations,
  activeId,
  onSelect
}: {
  conversations: ConversationStub[];
  activeId?: string;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="space-y-1">
      {conversations.map((c) => (
        <button
          key={c.id}
          onClick={() => onSelect(c.id)}
          className={`w-full rounded-md px-3 py-2 text-left text-sm ${
            c.id === activeId ? "bg-brand-50 text-brand-700" : "hover:bg-slate-100"
          }`}
        >
          <div className="font-medium">{c.contact_name}</div>
          <div className="text-xs text-slate-500">
            {c.last_message_at
              ? new Date(c.last_message_at).toLocaleString()
              : "No messages"}
          </div>
        </button>
      ))}
    </div>
  );
}