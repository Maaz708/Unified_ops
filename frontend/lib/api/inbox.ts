import { request } from "./client";

export function getInboxConversations(token: string) {
  return request<any[]>(`/inbox/conversations`, { token });
}

export function getConversationMessages(conversationId: string, token: string) {
  return request<any[]>(`/inbox/conversations/${conversationId}/messages`, { token });
}

export function sendStaffReply(conversationId: string, body: string, token: string) {
  return request(`/inbox/conversations/${conversationId}/messages`, {
    method: "POST",
    body: { body },
    token,
  });
}