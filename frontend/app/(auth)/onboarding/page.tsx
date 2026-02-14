import { WorkspaceOnboardingWizard } from "@/components/onboarding/WorkspaceOnboardingWizard";

export default function OnboardingPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="card w-full max-w-3xl p-6">
        <WorkspaceOnboardingWizard />
      </div>
    </main>
  );
}