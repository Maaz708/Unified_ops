"use client";

import { useEffect, useState } from "react";
import { ConversationList } from "./ConversationList";
import { MessageThread } from "./MessageThread";
import { ReplyBox } from "./ReplyBox";
import { getInboxConversations, getConversationMessages, sendStaffReply } from "@/lib/api/inbox";

export function InboxPageContent({ token }: { token: string }) {
  const [conversations, setConversations] = useState<any[]>([]);
  const [activeId, setActiveId] = useState<string | undefined>();
  const [messages, setMessages] = useState<any[]>([]);

  useEffect(() => {
    if (!token) return;
    void (async () => {
      const data = await getInboxConversations(token);
      setConversations(data);
      if (data[0]) setActiveId(data[0].id);
    })();
  }, [token]);

  useEffect(() => {
    if (!activeId || !token) return;
    void (async () => {
      const data = await getConversationMessages(activeId, token);
      setMessages(data);
    })();
  }, [activeId, token]);

  async function handleSend(body: string) {
    if (!activeId || !token) return;
    await sendStaffReply(activeId, body, token);
    const data = await getConversationMessages(activeId, token);
    setMessages(data);
  }

  return (
    <div className="grid h-full gap-4 lg:grid-cols-[280px,1fr]">
      <div className="card p-3">
        <h2 className="mb-2 text-sm font-semibold text-slate-700">Conversations</h2>
        <ConversationList
          conversations={conversations}
          activeId={activeId}
          onSelect={setActiveId}
        />
      </div>
      <div className="card flex flex-col p-3">
        <div className="flex-1 overflow-y-auto pb-3">
          <MessageThread messages={messages} />
        </div>
        <ReplyBox onSend={handleSend} />
      </div>
    </div>
  );
}