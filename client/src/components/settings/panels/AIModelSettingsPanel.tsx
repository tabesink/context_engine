"use client";

import * as React from "react";
import { ChevronRight, Circle, Eye, EyeOff, Lock, RefreshCw } from "lucide-react";
import { ProviderIconBadge } from "@/components/icons/ProviderIcon";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  settingsButtonClassName,
  settingsCompactButtonClassName,
  settingsInputClassName,
} from "@/components/settings/settings-controls";
import { aiSettingsApi } from "@/lib/api/ai-settings";
import { APIError } from "@/lib/api/client";
import { selectIsAdmin, useAuthStore } from "@/stores/auth-store";
import {
  mapProviders,
  profileDisplayName,
  providerCatalog,
  sortProfilesForProvider,
  statusLabel,
  type ProviderId,
} from "@/components/settings/panels/providerViewModel";

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof APIError) {
    const body = error.body as { detail?: unknown } | null;
    if (body && typeof body.detail === "string") return body.detail;
  }
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

export function AIModelSettingsPanel() {
  const isAdmin = useAuthStore(selectIsAdmin);
  const [settings, setSettings] = React.useState<Awaited<ReturnType<typeof aiSettingsApi.get>> | null>(null);
  const [selectedProviderId, setSelectedProviderId] = React.useState<ProviderId>("openai");
  const [loading, setLoading] = React.useState(true);
  const [refreshing, setRefreshing] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [secretInputs, setSecretInputs] = React.useState<Record<string, string>>({});
  const [secretBusyByName, setSecretBusyByName] = React.useState<Record<string, boolean>>({});
  const [showCredentialByName, setShowCredentialByName] = React.useState<Record<string, boolean>>({});
  const [lastUpdated, setLastUpdated] = React.useState<Date | null>(null);
  const profileListRef = React.useRef<HTMLDivElement | null>(null);

  const load = React.useCallback(async (showSpinner: boolean) => {
    if (showSpinner) setRefreshing(true);
    else setLoading(true);
    setError(null);
    try {
      const next = await aiSettingsApi.get();
      setSettings(next);
      setLastUpdated(new Date());
    } catch (nextError) {
      setError(getErrorMessage(nextError, "Failed to load provider settings"));
    } finally {
      if (showSpinner) setRefreshing(false);
      else setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    if (!isAdmin) return;
    const task = window.setTimeout(() => {
      void load(false);
    }, 0);
    return () => window.clearTimeout(task);
  }, [isAdmin, load]);

  const providers = React.useMemo(() => mapProviders(settings), [settings]);
  const activeProviderId = providers.some((provider) => provider.id === selectedProviderId)
    ? selectedProviderId
    : (providers[0]?.id ?? "openai");
  const selectedProvider = providers.find((provider) => provider.id === activeProviderId) ?? providers[0] ?? providerCatalog[0];
  const linkedProfiles = sortProfilesForProvider(settings?.profiles ?? [], selectedProvider.providerKind);
  const selectedSecretName = selectedProvider.secretName;
  const typedValue = selectedSecretName ? secretInputs[selectedSecretName] ?? "" : "";
  const secretBusy = selectedSecretName ? Boolean(secretBusyByName[selectedSecretName]) : false;
  const canSave = Boolean(selectedSecretName && typedValue.trim().length > 0 && !secretBusy);
  const showCredential = selectedSecretName ? Boolean(showCredentialByName[selectedSecretName]) : false;

  const onSaveSecret = async () => {
    if (!selectedSecretName) return;
    const value = typedValue.trim();
    if (!value) return;
    setSecretBusyByName((current) => ({ ...current, [selectedSecretName]: true }));
    setError(null);
    try {
      const next = await aiSettingsApi.setProviderSecret(selectedSecretName, { value });
      setSettings(next);
      setSecretInputs((current) => ({ ...current, [selectedSecretName]: "" }));
      setLastUpdated(new Date());
    } catch (nextError) {
      setError(getErrorMessage(nextError, `Failed to save ${selectedProvider.name} credential`));
    } finally {
      setSecretBusyByName((current) => ({ ...current, [selectedSecretName]: false }));
    }
  };

  const onClearSecret = async () => {
    if (!selectedSecretName) return;
    setSecretBusyByName((current) => ({ ...current, [selectedSecretName]: true }));
    setError(null);
    try {
      const next = await aiSettingsApi.clearProviderSecret(selectedSecretName);
      setSettings(next);
      setSecretInputs((current) => ({ ...current, [selectedSecretName]: "" }));
      setLastUpdated(new Date());
    } catch (nextError) {
      setError(getErrorMessage(nextError, `Failed to clear ${selectedProvider.name} credential`));
    } finally {
      setSecretBusyByName((current) => ({ ...current, [selectedSecretName]: false }));
    }
  };

  if (!isAdmin) {
    return (
      <div className="rounded-xl border border-border bg-background p-4">
        <p className="text-sm font-medium text-foreground">Admin access required</p>
        <p className="mt-1 text-xs text-muted-foreground">Sign in with an admin account to configure model providers.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <p className="text-sm font-medium text-foreground">Providers</p>
        <p className="mt-1 text-xs leading-4 text-muted-foreground">
          Configure provider credentials and model profiles used by Context Engine.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[360px_minmax(0,1fr)]">
        <section className="space-y-4">
          <div className="space-y-1">
            {loading
              ? Array.from({ length: 3 }).map((_, idx) => (
                  <div key={idx} className="h-[72px] animate-pulse rounded-lg bg-muted/40" />
                ))
              : providers.map((provider) => {
                  const selected = provider.id === selectedProvider.id;
                  return (
                    <button
                      key={provider.id}
                      type="button"
                      onClick={() => setSelectedProviderId(provider.id)}
                      className={`relative w-full rounded-lg px-3 py-[18px] text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                        selected ? "bg-primary/8" : "hover:bg-muted/50"
                      }`}
                    >
                      {selected ? <span className="absolute left-0 top-2 bottom-2 w-[3px] rounded-r bg-primary" aria-hidden /> : null}
                      <div className="flex items-center justify-between gap-3 pl-2">
                        <div className="flex min-w-0 items-center gap-3">
                          <ProviderIconBadge id={provider.id} size="sm" />
                          <div className="min-w-0">
                            <p className="text-sm font-medium text-foreground">{provider.name}</p>
                            <p className="mt-1 text-xs text-muted-foreground">
                              {provider.profileCount} {provider.profileCount === 1 ? "profile" : "profiles"}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {provider.status === "local" ? <Badge variant="muted">Local</Badge> : null}
                          <ChevronRight className="size-4 text-muted-foreground" aria-hidden />
                        </div>
                      </div>
                    </button>
                  );
                })}
          </div>

          <Separator />

          <div className="space-y-2">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Connection health</p>
            <div>
              {providers.map((provider) => (
                <div
                  key={`health-${provider.id}`}
                  className="flex items-center justify-between gap-2 border-b border-border/70 py-2.5 last:border-b-0"
                >
                  <div className="flex items-center gap-2">
                    <Circle
                      className={`size-2 fill-current ${
                        provider.status === "healthy" || provider.status === "local" ? "text-emerald-500" : "text-slate-400"
                      }`}
                    />
                    <span className="text-xs text-foreground">
                      {provider.name} · {statusLabel(provider.status)}
                    </span>
                  </div>
                  <span className="text-xs text-muted-foreground">{provider.profileCount}</span>
                </div>
              ))}
            </div>
            <p className="pt-1 text-[11px] text-muted-foreground">
              Last updated {lastUpdated ? lastUpdated.toLocaleTimeString() : "—"}
            </p>
          </div>
        </section>

        <section className="space-y-6">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3">
              <ProviderIconBadge id={selectedProvider.id} size="lg" />
              <div>
                <p className="text-base font-semibold text-foreground">{selectedProvider.name}</p>
                <p className="text-xs text-muted-foreground">
                  {selectedProvider.profileCount} {selectedProvider.profileCount === 1 ? "profile" : "profiles"}
                </p>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => void load(true)}
              disabled={loading || refreshing}
              className={`${settingsCompactButtonClassName} px-4`}
            >
              <RefreshCw className={`mr-2 size-3.5 ${refreshing ? "animate-spin" : ""}`} />
              Refresh status
            </Button>
          </div>

          <div className="space-y-3">
            <p className="text-sm font-medium text-foreground">Credentials</p>
            <div className="flex items-start gap-2 rounded-md bg-muted/45 px-3 py-2 text-xs leading-4 text-muted-foreground">
              <Lock className="mt-0.5 size-3.5 shrink-0" aria-hidden />
              <span>Keys are encrypted on the server and are never returned to the browser.</span>
            </div>

            {selectedProvider.requiresCredential && selectedSecretName ? (
              <>
                <div className="space-y-2">
                  <Label htmlFor={`provider-secret-${selectedSecretName}`} className="text-xs font-medium text-foreground">
                    Credential
                  </Label>
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                    <div className="relative flex-1">
                      <Input
                        id={`provider-secret-${selectedSecretName}`}
                        type={showCredential ? "text" : "password"}
                        value={typedValue}
                        onChange={(event) =>
                          setSecretInputs((current) => ({ ...current, [selectedSecretName]: event.target.value }))
                        }
                        placeholder={selectedProvider.credentialPlaceholder}
                        className={`${settingsInputClassName} pr-9`}
                        autoComplete="off"
                      />
                      <button
                        type="button"
                        onClick={() =>
                          setShowCredentialByName((current) => ({ ...current, [selectedSecretName]: !showCredential }))
                        }
                        className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground"
                        aria-label={showCredential ? "Hide credential" : "Show credential"}
                      >
                        {showCredential ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                      </button>
                    </div>
                    <div className="flex shrink-0 gap-2">
                      <Button type="button" onClick={() => void onSaveSecret()} disabled={!canSave} className={`${settingsButtonClassName} px-5`}>
                        {secretBusy ? "Saving..." : "Save key"}
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        onClick={() => void onClearSecret()}
                        disabled={secretBusy}
                        className={settingsButtonClassName}
                      >
                        Clear key
                      </Button>
                    </div>
                  </div>
                </div>
                <p className="text-xs leading-4 text-muted-foreground">{selectedProvider.helperText}</p>
              </>
            ) : (
              <p className="text-xs leading-4 text-muted-foreground">{selectedProvider.helperText}</p>
            )}
          </div>

          <div className="space-y-3" ref={profileListRef}>
            <div>
              <p className="text-sm font-medium text-foreground">Used by model profiles ({linkedProfiles.length})</p>
              <p className="mt-1 text-xs leading-4 text-muted-foreground">Enabled profiles that use this provider credential.</p>
            </div>

            {loading ? (
              <div className="space-y-2">
                <div className="h-10 animate-pulse rounded-md bg-muted/40" />
                <div className="h-10 animate-pulse rounded-md bg-muted/40" />
              </div>
            ) : linkedProfiles.length === 0 ? (
              <p className="text-xs text-muted-foreground">No enabled profiles for this provider.</p>
            ) : (
              <div className="overflow-hidden rounded-lg border border-border">
                {linkedProfiles.map((profile, index) => (
                  <div
                    key={profile.id}
                    className={`flex items-center justify-between gap-2 px-3 py-3 hover:bg-muted/35 ${
                      index > 0 ? "border-t border-border" : ""
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <Circle className="size-2 fill-emerald-500 text-emerald-500" />
                      <span className="text-sm text-foreground">{profileDisplayName(profile)}</span>
                    </div>
                    <ChevronRight className="size-4 text-muted-foreground" aria-hidden />
                  </div>
                ))}
              </div>
            )}

            <div className="flex justify-end">
              <Button
                type="button"
                variant="outline"
                size="sm"
                className={`${settingsCompactButtonClassName} px-3`}
                onClick={() => profileListRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" })}
              >
                Manage profiles
              </Button>
            </div>
          </div>
        </section>
      </div>

      {error ? <p className="text-sm text-destructive">{error}</p> : null}
    </div>
  );
}
