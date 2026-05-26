"use client";

import { AppPageFrame } from "@/components/layout/AppPageFrame";
import { AccountSettingsPanel } from "@/components/settings/panels/AccountSettingsPanel";

export default function SettingsUsersPage() {
  return (
    <AppPageFrame contentClassName="overflow-y-auto">
      <section className="mx-auto w-full max-w-5xl px-6 py-8 pb-24 md:px-8 md:py-10">
        <header className="mb-6">
          <h1 className="text-2xl font-semibold tracking-tight">Account settings</h1>
          <p className="mt-1 text-sm text-muted-foreground">Fallback page for user administration.</p>
        </header>
        <AccountSettingsPanel />
      </section>
    </AppPageFrame>
  );
}
