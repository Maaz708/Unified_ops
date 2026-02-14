"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Tabs } from "@/components/ui/Tabs";
import { apiOnboardWorkspace } from "@/lib/api/workspace";

export function WorkspaceOnboardingWizard() {
  const router = useRouter();
  const [step, setStep] = useState<"workspace" | "owner" | "email" | "booking">("workspace");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const [workspaceName, setWorkspaceName] = useState("");
  const [ownerEmail, setOwnerEmail] = useState("");
  const [ownerName, setOwnerName] = useState("");
  const [ownerPassword, setOwnerPassword] = useState("");
  const [fromEmail, setFromEmail] = useState("");
  const [bookingTypeName, setBookingTypeName] = useState("Default Service");
  const [bookingTypeSlug, setBookingTypeSlug] = useState("default");

  function formatValidationErrors(error: any): string {
    // Debug: Log the error structure
    console.log('Error structure:', error);
    console.log('Error type:', typeof error);
    
    // Handle stringified JSON errors (most common case)
    if (typeof error === 'string') {
      try {
        const parsed = JSON.parse(error);
        console.log('Parsed error:', parsed);
        
        if (Array.isArray(parsed)) {
          return parsed
            .map((err: any) => {
              console.log('Individual error:', err);
              return err.msg || JSON.stringify(err);
            })
            .join('\n');
        }
        
        if (parsed.detail && Array.isArray(parsed.detail)) {
          return parsed.detail
            .map((err: any) => {
              console.log('Individual error:', err);
              return err.msg || JSON.stringify(err);
            })
            .join('\n');
        }
      } catch (e) {
        console.log('JSON parse failed:', e);
        // Not JSON, return as is
        return error;
      }
    }
    
    if (error?.detail) {
      // Handle FastAPI validation error format
      if (Array.isArray(error.detail)) {
        return error.detail
          .map((err: any) => {
            console.log('Individual error:', err);
            return err.msg || JSON.stringify(err);
          })
          .join('\n');
      }
      return error.detail;
    }
    
    if (error?.message) {
      // Handle string message
      return error.message;
    }
    
    return "Onboarding failed. Please check your input and try again.";
  }

  async function handleSubmit() {
    setLoading(true);
    setResult(null);
    try {
      // Default: one availability slot (tomorrow 9am–5pm) so backend validation passes
      const start = new Date();
      start.setDate(start.getDate() + 1);
      start.setHours(9, 0, 0, 0);
      const end = new Date(start);
      end.setHours(17, 0, 0, 0);

      await apiOnboardWorkspace({
        workspace_name: workspaceName,
        owner: {
          email: ownerEmail,
          full_name: ownerName,
          password: ownerPassword
        },
        email_provider: {
          provider: "resend",
          from_email: fromEmail,
          from_name: workspaceName,
          api_key_alias: "default-resend"
        },
        booking_types: [
          {
            name: bookingTypeName,
            slug: bookingTypeSlug,
            description: "Default booking type",
            duration_minutes: 60
          }
        ],
        availability: [
          {
            booking_type_slug: bookingTypeSlug,
            staff_email: null,
            start_at: start.toISOString(),
            end_at: end.toISOString()
          }
        ]
      });
      setResult("Workspace created. You can now log in.");
      setSuccess(true);
    } catch (err: any) {
      const errorMessage = formatValidationErrors(err);
      setResult(errorMessage);
      setSuccess(false);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-semibold text-slate-900">Workspace onboarding</h1>
      <Tabs
        tabs={[
          { id: "workspace", label: "Workspace" },
          { id: "owner", label: "Owner" },
          { id: "email", label: "Email" },
          { id: "booking", label: "Booking" }
        ]}
        active={step}
        onChange={(id) => setStep(id as any)}
      />

      {step === "workspace" && (
        <div className="mt-4 space-y-3">
          <Input
            label="Workspace name"
            value={workspaceName}
            onChange={(e) => setWorkspaceName(e.target.value)}
          />
        </div>
      )}
      {step === "owner" && (
        <div className="mt-4 space-y-3">
          <Input label="Owner name" value={ownerName} onChange={(e) => setOwnerName(e.target.value)} />
          <Input
            label="Owner email"
            type="email"
            value={ownerEmail}
            onChange={(e) => setOwnerEmail(e.target.value)}
          />
          <Input
            label="Owner password"
            type="password"
            value={ownerPassword}
            onChange={(e) => setOwnerPassword(e.target.value)}
          />
        </div>
      )}
      {step === "email" && (
        <div className="mt-4 space-y-3">
          <Input
            label="From email"
            type="email"
            value={fromEmail}
            onChange={(e) => setFromEmail(e.target.value)}
          />
        </div>
      )}
      {step === "booking" && (
        <div className="mt-4 space-y-3">
          <Input
            label="Default booking type name"
            value={bookingTypeName}
            onChange={(e) => setBookingTypeName(e.target.value)}
          />
          <Input
            label="Slug"
            value={bookingTypeSlug}
            onChange={(e) => setBookingTypeSlug(e.target.value)}
          />
        </div>
      )}

      <div className="flex justify-between pt-2">
        <Button
          variant="ghost"
          onClick={() =>
            setStep((prev) =>
              prev === "workspace"
                ? "workspace"
                : prev === "owner"
                ? "workspace"
                : prev === "email"
                ? "owner"
                : "email"
            )
          }
        >
          Back
        </Button>
        <Button
          onClick={() =>
            step === "booking"
              ? void handleSubmit()
              : setStep(step === "workspace" ? "owner" : step === "owner" ? "email" : "booking")
          }
          disabled={loading}
        >
          {step === "booking" ? (loading ? "Creating..." : "Create workspace") : "Next"}
        </Button>
      </div>
      {result && (
        <div className="space-y-2">
          <p className={success ? "text-sm text-green-700" : "text-sm text-red-600"}>{result}</p>
          {success && (
            <Button type="button" onClick={() => router.push("/login")}>
              Go to Log in
            </Button>
          )}
        </div>
      )}
    </div>
  );
}