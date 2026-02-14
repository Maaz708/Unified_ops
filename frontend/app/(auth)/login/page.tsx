"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { apiAuthLogin } from "@/lib/api/auth";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showReset, setShowReset] = useState(false);
  const [resetEmail, setResetEmail] = useState("");
  const [resetLoading, setResetLoading] = useState(false);
  const [resetMessage, setResetMessage] = useState<string | null>(null);
  const router = useRouter();

  async function handlePasswordReset(e: React.FormEvent) {
    e.preventDefault();
    setResetLoading(true);
    setResetMessage(null);
    try {
      const response = await fetch('/api/v1/staff/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: resetEmail })
      });
      const data = await response.json();
      if (data.temp_password) {
        setResetMessage(`New temporary password: ${data.temp_password}`);
      } else {
        setResetMessage(data.message);
      }
    } catch (error) {
      setResetMessage("Failed to reset password");
    } finally {
      setResetLoading(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await apiAuthLogin({ email, password }) as { token: string; expires_in: number };
      if (res.token) {
        document.cookie = `auth_token=${res.token}; path=/; max-age=${res.expires_in ?? 86400}; samesite=lax`;
        // Full page redirect so the next request includes the cookie (client nav can miss it)
        window.location.href = "/dashboard";
        return;
      }
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="card w-full max-w-md p-6">
        <h1 className="text-lg font-semibold text-slate-900">Log in</h1>
        <p className="mt-1 text-sm text-slate-600">
          Staff and owners sign in to manage operations.
        </p>
        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Signing in..." : "Sign in"}
          </Button>
          <div className="mt-4 text-center">
            <button
              type="button"
              onClick={() => setShowReset(!showReset)}
              className="text-sm text-brand-600 hover:underline"
            >
              {showReset ? "Back to login" : "Forgot password?"}
            </button>
          </div>
        </form>

        {showReset && (
          <div className="mt-6 p-4 border border-slate-200 rounded-lg">
            <h3 className="text-sm font-medium text-slate-900 mb-3">Reset Password</h3>
            <form onSubmit={handlePasswordReset} className="space-y-3">
              <Input
                label="Email"
                type="email"
                value={resetEmail}
                onChange={(e) => setResetEmail(e.target.value)}
                required
              />
              {resetMessage && <p className="text-sm text-blue-600">{resetMessage}</p>}
              <Button type="submit" className="w-full" disabled={resetLoading}>
                {resetLoading ? "Resetting..." : "Reset Password"}
              </Button>
            </form>
          </div>
        )}
      </div>
    </main>
  );
}