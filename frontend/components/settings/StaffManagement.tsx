"use client";

import { useState, useEffect } from "react";
import { getStaffList, createStaff, updateStaff, deleteStaff } from "@/lib/api/staff";
import type { StaffOut, StaffCreate, StaffUpdate } from "@/lib/types/staff";
import { StaffRole } from "@/lib/types/staff";
import { StaffCredentials } from "./StaffCredentials";

export function StaffManagement({ workspaceId, token }: { workspaceId: string; token: string }) {
  const [staff, setStaff] = useState<StaffOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingStaff, setEditingStaff] = useState<StaffOut | null>(null);

  useEffect(() => {
    loadStaff();
  }, [workspaceId, token]);

  async function loadStaff() {
    try {
      const data = await getStaffList(workspaceId, token);
      setStaff(data);
    } catch (error) {
      console.error("Failed to load staff:", error);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(data: StaffCreate) {
    try {
      const result = await createStaff(workspaceId, data, token) as any;
      await loadStaff();
      setShowAddForm(false);
      
      // Add credentials to the display instead of alert
      if (result.temp_password && (window as any).addStaffCredentials) {
        (window as any).addStaffCredentials({
          email: result.email,
          tempPassword: result.temp_password,
          fullName: result.full_name,
          createdAt: result.created_at
        });
      }
    } catch (error) {
      console.error("Failed to create staff:", error);
      alert("Failed to create staff member");
    }
  }

  async function handleUpdate(staffId: string, data: StaffUpdate) {
    try {
      await updateStaff(workspaceId, staffId, data, token);
      await loadStaff();
      setEditingStaff(null);
    } catch (error) {
      console.error("Failed to update staff:", error);
      alert("Failed to update staff member");
    }
  }

  async function handleDelete(staffId: string) {
    if (!confirm("Are you sure you want to remove this staff member?")) return;
    
    try {
      await deleteStaff(workspaceId, staffId, token);
      await loadStaff();
    } catch (error) {
      console.error("Failed to delete staff:", error);
      alert("Failed to remove staff member");
    }
  }

  if (loading) {
    return <div className="text-sm text-slate-500">Loading staff...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-slate-900">Team Members</h3>
        <button
          onClick={() => setShowAddForm(true)}
          className="text-sm font-medium text-brand-600 hover:underline"
        >
          + Add Staff
        </button>
      </div>

      {staff.length === 0 ? (
        <p className="text-sm text-slate-500">No staff members added yet.</p>
      ) : (
        <div className="space-y-2">
          {staff.map((member) => (
            <div key={member.id} className="flex items-center justify-between p-3 border border-slate-200 rounded-lg">
              <div>
                <div className="font-medium text-slate-900">{member.full_name || member.email}</div>
                <div className="text-sm text-slate-500">{member.email}</div>
                <div className="text-xs text-slate-400">
                  {member.role === StaffRole.owner ? "Owner" : "Staff"} •{" "}
                  {member.is_active ? "Active" : "Inactive"}
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setEditingStaff(member)}
                  className="text-sm text-slate-600 hover:text-slate-900"
                >
                  Edit
                </button>
                {member.role !== StaffRole.owner && (
                  <button
                    onClick={() => handleDelete(member.id)}
                    className="text-sm text-red-600 hover:text-red-800"
                  >
                    Remove
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {(showAddForm || editingStaff) && (
        <StaffForm
          staff={editingStaff}
          onSubmit={editingStaff ? (data) => handleUpdate(editingStaff.id, data) : handleCreate}
          onCancel={() => {
            setShowAddForm(false);
            setEditingStaff(null);
          }}
        />
      )}
      
      <StaffCredentials />
    </div>
  );
}

function StaffForm({
  staff,
  onSubmit,
  onCancel,
}: {
  staff?: StaffOut | null;
  onSubmit: (data: any) => void;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState({
    email: staff?.email || "",
    full_name: staff?.full_name || "",
    role: staff?.role || StaffRole.staff,
    is_active: staff?.is_active ?? true,
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    onSubmit(formData);
  }

  return (
    <div className="border border-slate-200 rounded-lg p-4 space-y-4">
      <h4 className="font-medium text-slate-900">
        {staff ? "Edit Staff Member" : "Add New Staff Member"}
      </h4>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
          <input
            type="email"
            required
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-500"
            disabled={!!staff}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Full Name</label>
          <input
            type="text"
            value={formData.full_name}
            onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
            className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Role</label>
          <select
            value={formData.role}
            onChange={(e) => setFormData({ ...formData, role: e.target.value as StaffRole })}
            className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value={StaffRole.staff}>Staff</option>
            <option value={StaffRole.owner}>Owner</option>
          </select>
        </div>
        {staff && (
          <div className="flex items-center">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="mr-2"
            />
            <label htmlFor="is_active" className="text-sm text-slate-700">Active</label>
          </div>
        )}
        <div className="flex gap-2 pt-2">
          <button
            type="submit"
            className="px-4 py-2 bg-brand-600 text-white rounded-md hover:bg-brand-700"
          >
            {staff ? "Update" : "Add"}
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
