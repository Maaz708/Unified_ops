import { request } from "./client";
import type { InventoryCreate, InventoryOut, InventoryUpdate } from "@/lib/types/inventory";

export function getInventoryList(workspaceId: string, token?: string) {
  return request<InventoryOut[]>(`/inventory/${workspaceId}`, { token });
}

export function createInventoryItem(workspaceId: string, data: InventoryCreate, token?: string) {
  return request<InventoryOut>(`/inventory/${workspaceId}`, {
    method: "POST",
    body: data,
    token,
  });
}

export function updateInventoryItem(workspaceId: string, itemId: string, data: InventoryUpdate, token?: string) {
  return request<InventoryOut>(`/inventory/${workspaceId}/${itemId}`, {
    method: "PUT",
    body: data,
    token,
  });
}

export function deleteInventoryItem(workspaceId: string, itemId: string, token?: string) {
  return request<{ message: string }>(`/inventory/${workspaceId}/${itemId}`, {
    method: "DELETE",
    token,
  });
}

export function adjustInventoryQuantity(workspaceId: string, itemId: string, quantityChange: number, token?: string) {
  return request<{ message: string; old_quantity: number; new_quantity: number; change: number }>(
    `/inventory/${workspaceId}/${itemId}/adjust`,
    {
      method: "POST",
      body: quantityChange,
      token,
    }
  );
}
