"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";

interface StaffCredentials {
  email: string;
  tempPassword: string;
  fullName: string;
  createdAt: string;
}

export function StaffCredentials() {
  const [credentials, setCredentials] = useState<StaffCredentials[]>([]);

  // Load credentials from sessionStorage on mount
  useState(() => {
    const stored = sessionStorage.getItem("staffCredentials");
    if (stored) {
      setCredentials(JSON.parse(stored));
    }
  });

  const addCredentials = (staff: StaffCredentials) => {
    const updated = [staff, ...credentials].slice(0, 5); // Keep only last 5
    setCredentials(updated);
    sessionStorage.setItem("staffCredentials", JSON.stringify(updated));
  };

  const removeCredentials = (email: string) => {
    const updated = credentials.filter(c => c.email !== email);
    setCredentials(updated);
    sessionStorage.setItem("staffCredentials", JSON.stringify(updated));
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  // Export this function to be called from StaffManagement
  (window as any).addStaffCredentials = addCredentials;

  if (credentials.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-medium text-slate-900">Recent Staff Login Credentials</h3>
      <div className="space-y-3">
        {credentials.map((cred) => (
          <div key={cred.email} className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start justify-between mb-2">
              <div>
                <h4 className="font-medium text-slate-900">{cred.fullName}</h4>
                <p className="text-sm text-slate-600">{cred.email}</p>
                <p className="text-xs text-slate-500">Created: {new Date(cred.createdAt).toLocaleString()}</p>
              </div>
              <button
                onClick={() => removeCredentials(cred.email)}
                className="text-sm text-slate-400 hover:text-slate-600"
              >
                ×
              </button>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center justify-between bg-white rounded px-3 py-2 border border-blue-300">
                <span className="text-sm font-mono text-slate-700">{cred.tempPassword}</span>
                <button
                onClick={() => copyToClipboard(cred.tempPassword)}
                className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Copy
              </button>
              </div>
              
              <div className="flex gap-2">
                <button
                  onClick={() => copyToClipboard(`Email: ${cred.email}\nPassword: ${cred.tempPassword}`)}
                  className="px-2 py-1 text-xs border border-slate-300 rounded hover:bg-slate-50"
                >
                  Copy All
                </button>
                <button
                  onClick={() => copyToClipboard(cred.email)}
                  className="px-2 py-1 text-xs border border-slate-300 rounded hover:bg-slate-50"
                >
                  Copy Email
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      <p className="text-xs text-slate-500">
        These credentials are temporarily stored here for easy sharing. They will be cleared when you close this tab.
      </p>
    </div>
  );
}
