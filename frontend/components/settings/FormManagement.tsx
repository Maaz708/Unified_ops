"use client";

import { useState, useEffect } from "react";
import { getFormList, updateFormStatus, type FormOut } from "@/lib/api/forms";

export function FormManagement({ workspaceId, token }: { workspaceId: string; token: string }) {
  const [forms, setForms] = useState<FormOut[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadForms();
  }, [workspaceId, token]);

  async function loadForms() {
    try {
      const data = await getFormList(workspaceId, token);
      setForms(data);
    } catch (error) {
      console.error("Failed to load forms:", error);
    } finally {
      setLoading(false);
    }
  }

  async function toggleFormStatus(formId: string, active: boolean, stayActive: boolean) {
    try {
      await updateFormStatus(workspaceId, formId, { active, stay_active_after_submission: stayActive }, token);
      await loadForms();
    } catch (error) {
      console.error("Failed to update form:", error);
      alert("Failed to update form status");
    }
  }

  if (loading) {
    return <div className="text-sm text-slate-500">Loading forms...</div>;
  }

  if (forms.length === 0) {
    return <div className="text-sm text-slate-500">No forms created yet.</div>;
  }

  return (
    <div className="space-y-4">
      {forms.map((form) => (
        <div key={form.id} className="border border-slate-200 rounded-lg p-4">
          <div className="flex items-start justify-between mb-3">
            <div>
              <h3 className="font-medium text-slate-900">{form.name}</h3>
              {form.description && (
                <p className="text-sm text-slate-600 mt-1">{form.description}</p>
              )}
            </div>
            <div className={`px-2 py-1 rounded text-xs font-medium ${
              form.active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            }`}>
              {form.active ? 'Active' : 'Inactive'}
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-slate-700">Form Active</label>
              <button
                onClick={() => toggleFormStatus(form.id, !form.active, form.stay_active_after_submission)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  form.active ? 'bg-blue-600' : 'bg-slate-200'
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  form.active ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-slate-700">Stay Active After Submission</label>
                <p className="text-xs text-slate-500">Keep form accessible even after customer submits</p>
              </div>
              <button
                onClick={() => toggleFormStatus(form.id, form.active, !form.stay_active_after_submission)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  form.stay_active_after_submission ? 'bg-blue-600' : 'bg-slate-200'
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  form.stay_active_after_submission ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
