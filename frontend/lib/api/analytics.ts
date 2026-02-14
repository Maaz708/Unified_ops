import { request } from "./client";
import type { DashboardOverview, AiOperationalSummary } from "@/lib/types/analytics";

export function getDashboardOverview(workspaceId: string) {
  return request<DashboardOverview>(`/analytics/workspaces/${workspaceId}/overview`);
}

export function getAiOperationalSummary(workspaceId: string) {
  return request<AiOperationalSummary>(
    `/analytics/workspaces/${workspaceId}/ai-operational-summary`
  );
}