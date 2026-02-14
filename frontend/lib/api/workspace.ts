import { request } from "./client";

export function apiOnboardWorkspace(body: any) {
  return request(`/workspaces/onboard`, {
    method: "POST",
    body
  });
}

export interface WorkspaceEmailConfigOut {
  provider: string;
  from_email: string;
  from_name: string | null;
  api_key_alias: string;
  is_active: boolean;
}

export interface WorkspaceEmailConfigUpdate {
  from_email?: string;
  from_name?: string | null;
  api_key_alias?: string;
}

export function getWorkspaceEmailConfig(
  workspaceId: string,
  token: string
): Promise<WorkspaceEmailConfigOut> {
  return request<WorkspaceEmailConfigOut>(`/workspaces/${workspaceId}/email-config`, { token });
}

export function updateWorkspaceEmailConfig(
  workspaceId: string,
  body: WorkspaceEmailConfigUpdate,
  token: string
): Promise<WorkspaceEmailConfigOut> {
  return request<WorkspaceEmailConfigOut>(`/workspaces/${workspaceId}/email-config`, {
    method: "PATCH",
    body,
    token
  });
}

export interface WorkspaceValidation {
  communication_connected: boolean;
  has_booking_types: boolean;
  has_availability: boolean;
  can_activate: boolean;
  reasons: string[];
}

export interface WorkspaceStatusResponse {
  status: string;
  validation: WorkspaceValidation;
}

export function getWorkspaceStatus(
  workspaceId: string,
  token: string
): Promise<WorkspaceStatusResponse> {
  return request<WorkspaceStatusResponse>(`/workspaces/${workspaceId}/status`, { token });
}

export function activateWorkspace(
  workspaceId: string,
  token: string
): Promise<WorkspaceStatusResponse> {
  return request<WorkspaceStatusResponse>(`/workspaces/${workspaceId}/activate`, {
    method: "POST",
    token
  });
}

export interface AvailabilitySlotOut {
  id: string;
  booking_type_slug: string;
  booking_type_name: string;
  start_at: string;
  end_at: string;
  staff_name: string | null;
}

export interface AvailabilitySlotCreateRequest {
  booking_type_slug: string;
  start_at: string;
  end_at: string;
  staff_email?: string | null;
}

export function listAvailabilitySlots(
  workspaceId: string,
  token: string
): Promise<AvailabilitySlotOut[]> {
  return request<AvailabilitySlotOut[]>(`/workspaces/${workspaceId}/availability-slots`, { token });
}

export function createAvailabilitySlot(
  workspaceId: string,
  body: AvailabilitySlotCreateRequest,
  token: string
): Promise<AvailabilitySlotOut> {
  return request<AvailabilitySlotOut>(`/workspaces/${workspaceId}/availability-slots`, {
    method: "POST",
    body,
    token
  });
}

export function deleteAvailabilitySlot(
  workspaceId: string,
  slotId: string,
  token: string
): Promise<void> {
  return request<void>(`/workspaces/${workspaceId}/availability-slots/${slotId}`, {
    method: "DELETE",
    token
  });
}