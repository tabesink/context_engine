"use client";

import * as React from "react";
import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { aiSettingsApi } from "@/lib/api/ai-settings";
import { APIError } from "@/lib/api/client";
import { selectIsAdmin, useAuthStore } from "@/stores/auth-store";
import type { AIModelProfile, AISettingsResponse } from "@/types/ai-settings";

const panelClassName = "rounded-xl border border-[var(--border)] bg-[var(--background)] p-4";
const inputClassName = "h-9 rounded-full border-[var(--border)] bg-[var(--background)] shadow-none";
const selectTriggerClassName = "h-9 rounded-full border-[var(--border)] bg-[var(--background)] shadow-none";
const pillButtonClassName = "rounded-full shadow-none";
const providerSecrets = [
  { secretName: "OPENAI_API_KEY", label: "OpenAI", helper: "Used by OpenAI LLM and embedding profiles." },
  { secretName: "AWS_BEARER_TOKEN_BEDROCK", label: "AWS Bedrock", helper: "Used by Bedrock OpenAI-compatible LLM profiles." },
];

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof APIError) {
    const body = error.body as { detail?: unknown } | null;
    if (body && typeof body.detail === "string") return body.detail;
  }
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

function profileLabel(profile: AIModelProfile): string {
  const dims = profile.dimensions ? ` · ${profile.dimensions} dims` : "";
  return `${providerLabel(profile.provider)} · ${profile.model}${dims}`;
}

function providerLabel(provider: AIModelProfile["provider"]): string {
  if (provider === "bedrock_openai") return "bedrock";
  return provider;
}

export function AIModelSettingsPanel() {
  const isAdmin = useAuthStore(selectIsAdmin);
  const [settings, setSettings] = React.useState<AISettingsResponse | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [saveBusy, setSaveBusy] = React.useState(false);
  const [llmDefault, setLlmDefault] = React.useState<string>("");
  const [embeddingDefault, setEmbeddingDefault] = React.useState<string>("");
  const [secretInputs, setSecretInputs] = React.useState<Record<string, string>>({});
  const [secretBusyByName, setSecretBusyByName] = React.useState<Record<string, boolean>>({});

  const load = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const next = await aiSettingsApi.get();
      setSettings(next);
      setLlmDefault(next.defaults.llm_profile_id);
      setEmbeddingDefault(next.defaults.embedding_profile_id);
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

  const onSaveDefaults = async () => {
    setSaveBusy(true);
    setError(null);
    try {
      const next = await aiSettingsApi.updateDefaults({
        default_llm_profile_id: llmDefault,
        default_embedding_profile_id: embeddingDefault,
      });
      setSettings(next);
      setLlmDefault(next.defaults.llm_profile_id);
      setEmbeddingDefault(next.defaults.embedding_profile_id);
    } catch (nextError) {
      setError(getErrorMessage(nextError, "Failed to update defaults"));
    } finally {
      setSaveBusy(false);
    }
  };

  const setSecretInput = (secretName: string, value: string) => {
    setSecretInputs((current) => ({ ...current, [secretName]: value }));
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

  const onClearSecret = async (secretName: string) => {
    setSecretBusyByName((current) => ({ ...current, [secretName]: true }));
    setError(null);
    try {
      const next = await aiSettingsApi.clearProviderSecret(secretName);
      setSettings(next);
      setSecretInput(secretName, "");
    } catch (nextError) {
      setError(getErrorMessage(nextError, `Failed to clear ${secretName}`));
    } finally {
      setSecretBusyByName((current) => ({ ...current, [secretName]: false }));
    }
  };

  if (!isAdmin) {
    return (
      <div className={panelClassName}>
        <p className="text-sm font-medium text-[var(--foreground)]">Admin access required</p>
        <p className="mt-1 text-xs text-[var(--muted-foreground)]">
          Sign in with an admin account to configure model providers.
        </p>
      </div>
    );
  }

  const llmProfiles = (settings?.profiles ?? []).filter((item) => item.kind === "llm" && item.is_enabled);
  const embeddingProfiles = (settings?.profiles ?? []).filter(
    (item) => item.kind === "embedding" && item.is_enabled,
  );

  return (
    <div className="space-y-4">
      <div className={panelClassName}>
        <div className="mb-3 flex items-center justify-between gap-3">
          <p className="text-sm font-medium text-[var(--foreground)]">Current defaults</p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => void load()}
            disabled={loading}
            className={`${pillButtonClassName} px-4`}
          >
            <RefreshCw className={`mr-2 size-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
        {loading ? (
          <p className="text-sm text-[var(--muted-foreground)]">Loading AI settings...</p>
        ) : (
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="default-llm" className="text-xs font-medium text-[var(--foreground)]">
                Default LLM model
              </Label>
              <Select value={llmDefault} onValueChange={setLlmDefault}>
                <SelectTrigger id="default-llm" className={selectTriggerClassName}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="rounded-xl border-[var(--border)] shadow-none">
                  {llmProfiles.map((profile) => (
                    <SelectItem key={profile.id} value={profile.id}>
                      {profileLabel(profile)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="default-embedding" className="text-xs font-medium text-[var(--foreground)]">
                Default embedding model
              </Label>
              <Select value={embeddingDefault} onValueChange={setEmbeddingDefault}>
                <SelectTrigger id="default-embedding" className={selectTriggerClassName}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="rounded-xl border-[var(--border)] shadow-none">
                  {embeddingProfiles.map((profile) => (
                    <SelectItem key={profile.id} value={profile.id}>
                      {profileLabel(profile)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <p className="text-xs leading-4 text-[var(--muted-foreground)]">
              Embedding default changes apply only to new knowledge graph domains.
            </p>
            <div className="flex justify-end">
              <Button onClick={() => void onSaveDefaults()} disabled={saveBusy || loading} className={pillButtonClassName}>
                {saveBusy ? "Saving..." : "Save defaults"}
              </Button>
            </div>
          </div>
        )}
      </div>

      <div className={panelClassName}>
        <p className="mb-1 text-sm font-medium text-[var(--foreground)]">Provider keys</p>
        <p className="mb-3 text-xs leading-4 text-[var(--muted-foreground)]">
          Keys are encrypted on the server and are never returned to the browser.
        </p>
        <div className="space-y-3">
          {providerSecrets.map((provider) => {
            const status = settings?.secret_status[provider.secretName] ?? "missing";
            const busy = Boolean(secretBusyByName[provider.secretName]);
            return (
              <div key={provider.secretName} className="rounded-xl border border-[var(--border)] bg-[var(--secondary)]/25 p-3">
                <div className="mb-2 flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-[var(--foreground)]">{provider.label}</p>
                    <p className="text-xs text-[var(--muted-foreground)]">
                      {provider.secretName} · {status}
                    </p>
                  </div>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => void onClearSecret(provider.secretName)}
                    disabled={busy || status !== "present"}
                    className={`${pillButtonClassName} px-4`}
                  >
                    Clear
                  </Button>
                </div>
                <div className="flex flex-col gap-2 sm:flex-row">
                  <Input
                    type="password"
                    value={secretInputs[provider.secretName] || ""}
                    onChange={(event) => setSecretInput(provider.secretName, event.target.value)}
                    placeholder={status === "present" ? "Replace stored key" : "Enter API key"}
                    className={inputClassName}
                    autoComplete="off"
                  />
                  <Button
                    type="button"
                    onClick={() => void onSaveSecret(provider.secretName)}
                    disabled={busy || !(secretInputs[provider.secretName] || "").trim()}
                    className={`${pillButtonClassName} px-5`}
                  >
                    {busy ? "Saving..." : "Save"}
                  </Button>
                </div>
                <p className="mt-2 text-xs leading-4 text-[var(--muted-foreground)]">{provider.helper}</p>
              </div>
            );
          })}
          <div className="rounded-xl border border-[var(--border)] bg-[var(--secondary)]/25 p-3">
            <p className="text-sm font-medium text-[var(--foreground)]">Ollama</p>
            <p className="text-xs text-[var(--muted-foreground)]">
              No API key required. Configure Ollama profile endpoints in model profiles.
            </p>
          </div>
        </div>
      </div>

      <div className={panelClassName}>
        <p className="mb-2 text-sm font-medium text-[var(--foreground)]">Profiles</p>
        {settings ? (
          <div className="space-y-2">
            {settings.profiles.map((profile) => (
              <div key={profile.id} className="rounded-xl border border-[var(--border)] bg-[var(--secondary)]/25 px-3 py-2.5">
                <p className="text-sm font-medium text-[var(--foreground)]">
                  {profileLabel(profile)}
                  {profile.is_default ? " · default" : ""}
                </p>
                <p className="text-xs text-[var(--muted-foreground)]">
                  {profile.kind}
                  {!profile.is_enabled ? " · disabled" : ""}
                  {profile.api_key_status !== "not_required" ? ` · key ${profile.api_key_status}` : ""}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-[var(--muted-foreground)]">Loading profiles...</p>
        )}
      </div>

      {error ? <p className="text-sm text-destructive">{error}</p> : null}
    </div>
  );
}

