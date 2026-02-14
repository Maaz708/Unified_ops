"use client";

import { useState, useEffect } from "react";
import { getInventoryList, createInventoryItem, updateInventoryItem, deleteInventoryItem, adjustInventoryQuantity } from "@/lib/api/inventory";
import type { InventoryOut, InventoryCreate, InventoryUpdate } from "@/lib/types/inventory";

export function InventoryManagement({ workspaceId, token }: { workspaceId: string; token: string }) {
  const [items, setItems] = useState<InventoryOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingItem, setEditingItem] = useState<InventoryOut | null>(null);

  useEffect(() => {
    loadItems();
  }, [workspaceId, token]);

  async function loadItems() {
    try {
      const data = await getInventoryList(workspaceId, token);
      setItems(data);
    } catch (error) {
      console.error("Failed to load inventory:", error);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(data: InventoryCreate) {
    try {
      await createInventoryItem(workspaceId, data, token);
      await loadItems();
      setShowAddForm(false);
    } catch (error) {
      console.error("Failed to create item:", error);
      alert("Failed to create inventory item");
    }
  }

  async function handleUpdate(itemId: string, data: InventoryUpdate) {
    try {
      await updateInventoryItem(workspaceId, itemId, data, token);
      await loadItems();
      setEditingItem(null);
    } catch (error) {
      console.error("Failed to update item:", error);
      alert("Failed to update inventory item");
    }
  }

  async function handleDelete(itemId: string) {
    if (!confirm("Are you sure you want to delete this inventory item?")) return;
    
    try {
      await deleteInventoryItem(workspaceId, itemId, token);
      await loadItems();
    } catch (error) {
      console.error("Failed to delete item:", error);
      alert("Failed to delete inventory item");
    }
  }

  async function handleAdjustQuantity(itemId: string, change: number) {
    try {
      await adjustInventoryQuantity(workspaceId, itemId, change, token);
      await loadItems();
    } catch (error) {
      console.error("Failed to adjust quantity:", error);
      alert("Failed to adjust quantity");
    }
  }

  if (loading) {
    return <div className="text-sm text-slate-500">Loading inventory...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-slate-900">Inventory Items</h3>
        <button
          onClick={() => setShowAddForm(true)}
          className="text-sm font-medium text-brand-600 hover:underline"
        >
          + Add Item
        </button>
      </div>

      {items.length === 0 ? (
        <p className="text-sm text-slate-500">No inventory items added yet.</p>
      ) : (
        <div className="space-y-2">
          {items.map((item) => (
            <div key={item.id} className="flex items-center justify-between p-3 border border-slate-200 rounded-lg">
              <div className="flex-1">
                <div className="font-medium text-slate-900">{item.name}</div>
                <div className="text-sm text-slate-500">SKU: {item.sku}</div>
                {item.description && (
                  <div className="text-xs text-slate-400 mt-1">{item.description}</div>
                )}
                <div className="flex items-center gap-4 mt-2">
                  <span className={`text-sm font-medium ${
                    item.current_quantity <= (item.reorder_threshold || 0) 
                      ? "text-red-600" 
                      : "text-green-600"
                  }`}>
                    {item.current_quantity} {item.unit || "units"}
                  </span>
                  {item.reorder_threshold && (
                    <span className="text-xs text-slate-500">
                      Reorder at: {item.reorder_threshold} {item.unit || "units"}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handleAdjustQuantity(item.id, -1)}
                    className="w-6 h-6 text-slate-600 hover:bg-slate-100 rounded flex items-center justify-center text-sm"
                  >
                    -
                  </button>
                  <button
                    onClick={() => handleAdjustQuantity(item.id, 1)}
                    className="w-6 h-6 text-slate-600 hover:bg-slate-100 rounded flex items-center justify-center text-sm"
                  >
                    +
                  </button>
                </div>
                <button
                  onClick={() => setEditingItem(item)}
                  className="text-sm text-slate-600 hover:text-slate-900"
                >
                  Edit
                </button>
                <button
                  onClick={() => handleDelete(item.id)}
                  className="text-sm text-red-600 hover:text-red-800"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {(showAddForm || editingItem) && (
        <InventoryForm
          item={editingItem}
          onSubmit={editingItem ? (data) => handleUpdate(editingItem.id, data) : handleCreate}
          onCancel={() => {
            setShowAddForm(false);
            setEditingItem(null);
          }}
        />
      )}
    </div>
  );
}

function InventoryForm({
  item,
  onSubmit,
  onCancel,
}: {
  item?: InventoryOut | null;
  onSubmit: (data: any) => void;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState({
    sku: item?.sku || "",
    name: item?.name || "",
    description: item?.description || "",
    current_quantity: item?.current_quantity || 0,
    reorder_threshold: item?.reorder_threshold || undefined,
    unit: item?.unit || "",
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    onSubmit(formData);
  }

  return (
    <div className="border border-slate-200 rounded-lg p-4 space-y-4">
      <h4 className="font-medium text-slate-900">
        {item ? "Edit Inventory Item" : "Add New Inventory Item"}
      </h4>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">SKU *</label>
            <input
              type="text"
              required
              value={formData.sku}
              onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Name *</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
          <textarea
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-500"
            rows={2}
          />
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Current Quantity *</label>
            <input
              type="number"
              required
              min="0"
              value={formData.current_quantity}
              onChange={(e) => setFormData({ ...formData, current_quantity: parseInt(e.target.value) || 0 })}
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Reorder Threshold</label>
            <input
              type="number"
              min="0"
              value={formData.reorder_threshold || ""}
              onChange={(e) => setFormData({ ...formData, reorder_threshold: e.target.value ? parseInt(e.target.value) : undefined })}
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Unit</label>
            <input
              type="text"
              value={formData.unit}
              onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
              placeholder="e.g., units, boxes, kg"
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
        </div>
        <div className="flex gap-2 pt-2">
          <button
            type="submit"
            className="px-4 py-2 bg-brand-600 text-white rounded-md hover:bg-brand-700"
          >
            {item ? "Update" : "Add"}
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 border border-slate-300 text-slate-700 rounded-md hover:bg-slate-50"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
