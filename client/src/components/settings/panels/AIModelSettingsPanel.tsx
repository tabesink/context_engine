"use client";

import * as React from "react";
import { ChevronRight, Eye, EyeOff } from "lucide-react";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { aiSettingsApi } from "@/lib/api/ai-settings";
import { APIError } from "@/lib/api/client";
import { selectIsAdmin, useAuthStore } from "@/stores/auth-store";
import type { AISettingsResponse, ProviderKind } from "@/types/ai-settings";

const panelClassName = "rounded-lg border border-neutral-200 bg-white p-4 shadow-none";
const tileClassName =
  "grid min-h-28 grid-rows-[1fr_auto] gap-4 rounded-lg border border-neutral-200 bg-white p-4 shadow-none transition-colors hover:bg-neutral-50 hover:border-neutral-300";
const iconButtonClassName =
  "h-8 w-8 rounded-md border border-transparent text-neutral-500 hover:border-neutral-200 hover:bg-neutral-50 hover:text-neutral-800";
const metaClassName = "text-[12px] font-mono text-neutral-500";
const statusClassName = "inline-flex items-center gap-1.5 text-xs font-medium text-neutral-700";
const inputClassName =
  "h-8 rounded-none border-0 border-b border-neutral-300 bg-neutral-50 px-2 text-sm text-neutral-900 shadow-none placeholder:text-neutral-400 focus-visible:border-neutral-500 focus-visible:ring-0";
const providerSecrets = [
  {
    provider: "openai" as ProviderKind,
    secretName: "OPENAI_API_KEY",
    label: "OpenAI",
  },
  {
    provider: "bedrock_openai" as ProviderKind,
    secretName: "AWS_BEARER_TOKEN_BEDROCK",
    label: "AWS Bedrock",
  },
];

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof APIError) {
    const body = error.body as { detail?: unknown } | null;
    if (body && typeof body.detail === "string") return body.detail;
  }
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

function countLabel(count: number, singular: string, plural: string): string {
  return `${count} ${count === 1 ? singular : plural}`;
}

function providerStatusLabel(provider: ProviderKind, secretStatus: "present" | "missing"): string {
  if (provider === "ollama") return "Local";
  if (secretStatus === "present") return "Ready";
  return "Missing key";
}

function providerStatusDotClass(provider: ProviderKind, secretStatus: "present" | "missing"): string {
  if (provider === "ollama") return "bg-emerald-500";
  if (secretStatus === "present") return "bg-emerald-500";
  return "bg-red-500";
}

function ProviderLogo({ provider, size = 40 }: { provider: ProviderKind; size?: number }) {
  if (provider === "bedrock_openai") {
    return (
      <Image
        src="/aws_logo_transparent.png"
        alt="AWS logo"
        width={size}
        height={size}
        unoptimized
        className="object-contain"
        style={{ height: size, width: size }}
      />
    );
  }

  if (provider === "ollama") {
    return (
      <Image
        src="/ollama_logo_transparent.png"
        alt="Ollama logo"
        width={size}
        height={size}
        unoptimized
        className="object-contain"
        style={{ height: size, width: size }}
      />
    );
  }

  return (
    <Image
      src="/openai_logo.svg"
      alt="OpenAI logo"
      width={size}
      height={size}
      unoptimized
      className="object-contain"
      style={{ height: size, width: size }}
    />
  );
}

export function AIModelSettingsPanel() {
  const isAdmin = useAuthStore(selectIsAdmin);
  const [settings, setSettings] = React.useState<AISettingsResponse | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [secretInputs, setSecretInputs] = React.useState<Record<string, string>>({});
  const [secretBusyByName, setSecretBusyByName] = React.useState<Record<string, boolean>>({});
  const [secretVisibleByName, setSecretVisibleByName] = React.useState<Record<string, boolean>>({});

  const load = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const next = await aiSettingsApi.get();
      setSettings(next);
    } catch (nextError) {
      setError(getErrorMessage(nextError, "Failed to load AI settings"));
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    if (!isAdmin) return;
    const task = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(task);
  }, [isAdmin, load]);

  const setSecretInput = (secretName: string, value: string) => {
    setSecretInputs((current) => ({ ...current, [secretName]: value }));
  };

  const toggleSecretVisible = (secretName: string) => {
    setSecretVisibleByName((current) => ({ ...current, [secretName]: !current[secretName] }));
  };

  const onSaveSecret = async (secretName: string) => {
    const value = (secretInputs[secretName] || "").trim();
    if (!value) return;
    setSecretBusyByName((current) => ({ ...current, [secretName]: true }));
    setError(null);
    try {
      const next = await aiSettingsApi.setProviderSecret(secretName, { value });
      setSettings(next);
      setSecretInput(secretName, "");
    } catch (nextError) {
      setError(getErrorMessage(nextError, `Failed to save ${secretName}`));
    } finally {
      setSecretBusyByName((current) => ({ ...current, [secretName]: false }));
    }
  };

  if (!isAdmin) {
    return (
      <div className={panelClassName}>
        <p className="text-sm font-medium text-neutral-900">Admin access required</p>
        <p className="mt-1 text-xs text-neutral-600">
          Sign in with an admin account to configure model providers.
        </p>
      </div>
    );
  }

  const profiles = settings?.profiles ?? [];
  const openAiProfileCount = profiles.filter((item) => item.provider === "openai" && item.is_enabled).length;
  const bedrockProfileCount = profiles.filter((item) => item.provider === "bedrock_openai" && item.is_enabled).length;
  const ollamaProfileCount = profiles.filter((item) => item.provider === "ollama" && item.is_enabled).length;
  const openAiSecretStatus = settings?.secret_status.OPENAI_API_KEY ?? "missing";
  const bedrockSecretStatus = settings?.secret_status.AWS_BEARER_TOKEN_BEDROCK ?? "missing";

  return (
    <div className="space-y-6">
      <section className="space-y-3">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-medium text-neutral-900">Provider overview</p>
            <p className="mt-1 text-xs leading-4 text-neutral-600">
              Configure retrieval providers and monitor key status.
            </p>
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          <Card className={tileClassName}>
            <div className="grid grid-cols-[44px_minmax(0,1fr)_32px] items-start gap-3">
              <div className="grid h-10 w-10 place-items-center">
                <ProviderLogo provider="openai" />
              </div>
              <p className="truncate pt-1 text-sm font-medium text-neutral-900">OpenAI</p>
              <Button type="button" variant="ghost" size="icon-sm" className={iconButtonClassName} aria-label="Open OpenAI details">
                <ChevronRight className="size-4" />
              </Button>
            </div>

            <div className="flex items-end justify-between gap-2">
              <p className={metaClassName}>{countLabel(openAiProfileCount, "profile", "profiles")}</p>
              <p className={statusClassName}>
                <span className={`h-1.5 w-1.5 rounded-full ${providerStatusDotClass("openai", openAiSecretStatus)}`} aria-hidden />
                {providerStatusLabel("openai", openAiSecretStatus)}
              </p>
            </div>
          </Card>

          <Card className={tileClassName}>
            <div className="grid grid-cols-[44px_minmax(0,1fr)_32px] items-start gap-3">
              <div className="grid h-10 w-10 place-items-center">
                <ProviderLogo provider="bedrock_openai" />
              </div>
              <p className="truncate pt-1 text-sm font-medium text-neutral-900">AWS Bedrock</p>
              <Button type="button" variant="ghost" size="icon-sm" className={iconButtonClassName} aria-label="Open AWS Bedrock details">
                <ChevronRight className="size-4" />
              </Button>
            </div>

            <div className="flex items-end justify-between gap-2">
              <p className={metaClassName}>{countLabel(bedrockProfileCount, "profile", "profiles")}</p>
              <p className={statusClassName}>
                <span className={`h-1.5 w-1.5 rounded-full ${providerStatusDotClass("bedrock_openai", bedrockSecretStatus)}`} aria-hidden />
                {providerStatusLabel("bedrock_openai", bedrockSecretStatus)}
              </p>
            </div>
          </Card>

          <Card className={tileClassName}>
            <div className="grid grid-cols-[44px_minmax(0,1fr)_32px] items-start gap-3">
              <div className="grid h-10 w-10 place-items-center">
                <ProviderLogo provider="ollama" />
              </div>
              <p className="truncate pt-1 text-sm font-medium text-neutral-900">Ollama</p>
              <Button type="button" variant="ghost" size="icon-sm" className={iconButtonClassName} aria-label="Open Ollama details">
                <ChevronRight className="size-4" />
              </Button>
            </div>

            <div className="flex items-end justify-between gap-2">
              <p className={metaClassName}>{countLabel(ollamaProfileCount, "profile", "profiles")} · no key required</p>
              <p className={statusClassName}>
                <span className={`h-1.5 w-1.5 rounded-full ${providerStatusDotClass("ollama", "present")}`} aria-hidden />
                {providerStatusLabel("ollama", "present")}
              </p>
            </div>
          </Card>
        </div>
      </section>

      <section className="space-y-3">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-medium text-neutral-900">Credential management</p>
            <p className="mt-1 text-xs leading-4 text-neutral-600">
              Save write-only credentials for external providers.
            </p>
          </div>
          <p className="mt-0.5 text-xs text-neutral-500">Encrypted server-side</p>
        </div>

        <div className="space-y-2.5">
          {providerSecrets.map((provider) => {
            const busy = Boolean(secretBusyByName[provider.secretName]);
            const typedValue = secretInputs[provider.secretName] || "";
            const canSave = typedValue.trim().length > 0 && !busy;
            const isVisible = Boolean(secretVisibleByName[provider.secretName]);

            return (
              <Card key={provider.secretName} className="grid gap-3 rounded-lg border-neutral-200 bg-white p-4 shadow-none md:grid-cols-[180px_minmax(0,1fr)_auto] md:items-center">
                <div className="flex h-full items-center gap-2.5 self-center">
                  <div className="grid h-8 w-8 place-items-center">
                    <ProviderLogo provider={provider.provider} size={32} />
                  </div>
                  <p className="text-sm font-medium text-neutral-900">{provider.label}</p>
                </div>

                <div>
                  <div className="relative">
                    <Input
                      id={`provider-secret-${provider.secretName}`}
                      type={isVisible ? "text" : "password"}
                      value={typedValue}
                      onChange={(event) => setSecretInput(provider.secretName, event.target.value)}
                      placeholder="Enter API Key..."
                      className={`${inputClassName} pr-9`}
                      autoComplete="off"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      onClick={() => toggleSecretVisible(provider.secretName)}
                      className="absolute right-0 top-0 h-8 w-8 rounded-md border border-transparent text-neutral-500 hover:border-neutral-200 hover:bg-neutral-50 hover:text-neutral-800"
                      aria-label={isVisible ? `Hide ${provider.label} credential` : `Show ${provider.label} credential`}
                    >
                      {isVisible ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                    </Button>
                  </div>
                </div>

                <Button
                  type="button"
                  size="sm"
                  onClick={() => void onSaveSecret(provider.secretName)}
                  disabled={!canSave}
                  className="h-8 rounded-md border border-neutral-950 bg-neutral-950 px-3 text-white shadow-none hover:bg-neutral-800"
                >
                  {busy ? "Saving..." : "Save"}
                </Button>
              </Card>
            );
          })}
        </div>
      </section>

      {loading ? (
        <p className="text-xs text-neutral-500">Loading provider settings...</p>
      ) : null}

      {error ? (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      ) : null}
    </div>
  );
}
