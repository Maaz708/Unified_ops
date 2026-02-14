export interface LowStockItem {
    id: string;
    sku: string;
    name: string;
    current_quantity: number;
    reorder_threshold?: number;
    unit?: string;
  }

export interface InventoryCreate {
  sku: string;
  name: string;
  description?: string;
  current_quantity: number;
  reorder_threshold?: number;
  unit?: string;
}

export interface InventoryUpdate {
  sku?: string;
  name?: string;
  description?: string;
  current_quantity?: number;
  reorder_threshold?: number;
  unit?: string;
}

export interface InventoryOut {
  id: string;
  sku: string;
  name: string;
  description?: string;
  current_quantity: number;
  reorder_threshold?: number;
  unit?: string;
  created_at: string;
  updated_at: string;
}