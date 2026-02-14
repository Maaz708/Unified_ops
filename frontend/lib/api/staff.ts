import { request } from "./client";
import type { StaffCreate, StaffOut, StaffUpdate } from "@/lib/types/staff";

export function getStaffList(workspaceId: string, token?: string) {
  return request<StaffOut[]>(`/staff/${workspaceId}`, { token });
}

export function createStaff(workspaceId: string, data: StaffCreate, token?: string) {
  return request<StaffOut>(`/staff/${workspaceId}`, {
    method: "POST",
    body: data,
    token,
  });
}

export function updateStaff(workspaceId: string, staffId: string, data: StaffUpdate, token?: string) {
  return request<StaffOut>(`/staff/${workspaceId}/${staffId}`, {
    method: "PUT",
    body: data,
    token,
  });
}

export function deleteStaff(workspaceId: string, staffId: string, token?: string) {
  return request<{ message: string }>(`/staff/${workspaceId}/${staffId}`, {
    method: "DELETE",
    token,
  });
}
