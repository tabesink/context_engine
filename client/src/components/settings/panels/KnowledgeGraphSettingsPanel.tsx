"use client";

import * as React from "react";
import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { aiSettingsApi } from "@/lib/api/ai-settings";
import { APIError } from "@/lib/api/client";
import {
  knowledgeGraphAdminApi,
  type CreateKnowledgeGraphDomainPayload,
  type KnowledgeGraphDomain,
} from "@/lib/api/knowledge-graph-admin";
import { selectIsAdmin, useAuthStore } from "@/stores/auth-store";
import type { AIModelProfile } from "@/types/ai-settings";

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof APIError) {
    const body = error.body as { detail?: unknown } | null;
    if (body && typeof body.detail === "string") return body.detail;
  }
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

type DomainAction = "up" | "down" | "recreate" | "regenerate" | "archive";

const panelClassName = "rounded-xl border border-[var(--border)] bg-[var(--secondary)]/35 p-4";
const inputClassName = "h-9 rounded-full border-[var(--border)] bg-[var(--background)] shadow-none";
const selectTriggerClassName = "h-9 rounded-full border-[var(--border)] bg-[var(--background)] shadow-none";
const pillButtonClassName = "rounded-full shadow-none";
const retrievalDefaultsInputClassName = "h-9 rounded-full border-[var(--border)] bg-[var(--background)] shadow-none";

function embeddingProfileLabel(profile: AIModelProfile): string {
  const dims = profile.dimensions ? ` · ${profile.dimensions} dims` : "";
  return `${profile.provider} · ${profile.model}${dims}`;
}

function parsePositiveInt(value: string): number | undefined {
  const parsed = Number.parseInt(value.trim(), 10);
  if (!Number.isInteger(parsed) || parsed < 1) return undefined;
  return parsed;
}

export function KnowledgeGraphSettingsPanel() {
  const isAdmin = useAuthStore(selectIsAdmin);
  const [domains, setDomains] = React.useState<KnowledgeGraphDomain[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [actionBusyByDomain, setActionBusyByDomain] = React.useState<Record<string, DomainAction | null>>({});
  const [createBusy, setCreateBusy] = React.useState(false);
  const [newDomainId, setNewDomainId] = React.useState("");
  const [newDisplayName, setNewDisplayName] = React.useState("");
  const [newHostPort, setNewHostPort] = React.useState("");
  const [newTopK, setNewTopK] = React.useState("10");
  const [newChunkTopK, setNewChunkTopK] = React.useState("10");
  const [newChunkRerankTopK, setNewChunkRerankTopK] = React.useState("10");
  const [newTextUnitTokens, setNewTextUnitTokens] = React.useState("4000");
  const [newGlobalTokens, setNewGlobalTokens] = React.useState("4000");
  const [newLocalTokens, setNewLocalTokens] = React.useState("4000");
  const [embeddingProfiles, setEmbeddingProfiles] = React.useState<AIModelProfile[]>([]);
  const [selectedEmbeddingProfileId, setSelectedEmbeddingProfileId] = React.useState("");

  const loadDomains = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await knowledgeGraphAdminApi.list();
      setDomains(list);
    } catch (nextError) {
      setError(getErrorMessage(nextError, "Failed to load knowledge graph domains"));
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    if (!isAdmin) return;
    const task = window.setTimeout(() => {
      void loadDomains();
    }, 0);
    return () => window.clearTimeout(task);
  }, [isAdmin, loadDomains]);

  React.useEffect(() => {
    if (!isAdmin) return;
    const task = window.setTimeout(async () => {
      try {
        const settings = await aiSettingsApi.get();
        const enabledEmbeddings = settings.profiles.filter(
          (profile) => profile.kind === "embedding" && profile.is_enabled,
        );
        setEmbeddingProfiles(enabledEmbeddings);
        setSelectedEmbeddingProfileId(settings.defaults.embedding_profile_id);
      } catch {
        // Load/create flow handles surfaced API errors.
      }
    }, 0);
    return () => window.clearTimeout(task);
  }, [isAdmin]);

  const runAction = async (domainId: string, action: DomainAction) => {
    setActionBusyByDomain((prev) => ({ ...prev, [domainId]: action }));
    setError(null);
    try {
      if (action === "up") await knowledgeGraphAdminApi.up(domainId);
      if (action === "down") await knowledgeGraphAdminApi.down(domainId);
      if (action === "recreate") await knowledgeGraphAdminApi.recreate(domainId);
      if (action === "regenerate") await knowledgeGraphAdminApi.regenerate(domainId);
      if (action === "archive") await knowledgeGraphAdminApi.remove(domainId);
      await loadDomains();
    } catch (nextError) {
      setError(getErrorMessage(nextError, `Failed to ${action} domain`));
    } finally {
      setActionBusyByDomain((prev) => ({ ...prev, [domainId]: null }));
    }
  };

  const onCreate = async (event: React.FormEvent) => {
    event.preventDefault();
    const domainId = newDomainId.trim();
    const displayName = newDisplayName.trim();
    const hostPortRaw = newHostPort.trim();
    const parsedHostPort = hostPortRaw ? Number.parseInt(hostPortRaw, 10) : undefined;
    if (!domainId) return;
    const invalidHostPort =
      hostPortRaw !== "" && (!Number.isInteger(parsedHostPort) || parsedHostPort === undefined || parsedHostPort < 1 || parsedHostPort > 65535);
    if (invalidHostPort) {
      setError("Host port must be an integer between 1 and 65535");
      return;
    }
    if (!selectedEmbeddingProfileId) {
      setError("Select an embedding model before creating a domain");
      return;
    }
    const topK = parsePositiveInt(newTopK);
    const chunkTopK = parsePositiveInt(newChunkTopK);
    const chunkRerankTopK = parsePositiveInt(newChunkRerankTopK);
    const textUnitTokens = parsePositiveInt(newTextUnitTokens);
    const globalTokens = parsePositiveInt(newGlobalTokens);
    const localTokens = parsePositiveInt(newLocalTokens);
    if (
      !topK ||
      !chunkTopK ||
      !chunkRerankTopK ||
      !textUnitTokens ||
      !globalTokens ||
      !localTokens
    ) {
      setError("Retrieval defaults must be positive integers");
      return;
    }
    setCreateBusy(true);
    setError(null);
    const payload: CreateKnowledgeGraphDomainPayload = {
      domain_id: domainId,
      display_name: displayName || undefined,
      host_port: parsedHostPort,
      embedding_profile_id: selectedEmbeddingProfileId,
      top_k: topK,
      chunk_top_k: chunkTopK,
      chunk_rerank_top_k: chunkRerankTopK,
      max_token_for_text_unit: textUnitTokens,
      max_token_for_global_context: globalTokens,
      max_token_for_local_context: localTokens,
    };
    try {
      await knowledgeGraphAdminApi.create(payload);
      setNewDomainId("");
      setNewDisplayName("");
      setNewHostPort("");
      setNewTopK("10");
      setNewChunkTopK("10");
      setNewChunkRerankTopK("10");
      setNewTextUnitTokens("4000");
      setNewGlobalTokens("4000");
      setNewLocalTokens("4000");
      await loadDomains();
    } catch (nextError) {
      setError(getErrorMessage(nextError, "Failed to create domain"));
    } finally {
      setCreateBusy(false);
    }
  };

  if (!isAdmin) {
    return (
      <div className={panelClassName}>
        <p className="text-sm font-medium text-[var(--foreground)]">Admin access required</p>
        <p className="mt-1 text-xs text-[var(--muted-foreground)]">
          Sign in with an admin account to manage knowledge graph domains.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <form onSubmit={onCreate} className={panelClassName}>
        <p className="mb-3 text-sm font-medium text-[var(--foreground)]">Create domain</p>
        <div className="space-y-3">
          <div className="space-y-1.5">
            <Label htmlFor="kg-domain-id" className="text-xs font-medium text-[var(--foreground)]">
              Domain ID
            </Label>
            <Input
              id="kg-domain-id"
              placeholder="fatigue"
              value={newDomainId}
              onChange={(event) => setNewDomainId(event.target.value)}
              className={inputClassName}
              required
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="kg-display-name" className="text-xs font-medium text-[var(--foreground)]">
              Display name
            </Label>
            <Input
              id="kg-display-name"
              placeholder="Fatigue Manuals"
              value={newDisplayName}
              onChange={(event) => setNewDisplayName(event.target.value)}
              className={inputClassName}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="kg-host-port" className="text-xs font-medium text-[var(--foreground)]">
              Host port
            </Label>
            <Input
              id="kg-host-port"
              type="number"
              min={1}
              max={65535}
              placeholder="Auto (96xx)"
              value={newHostPort}
              onChange={(event) => setNewHostPort(event.target.value)}
              className={inputClassName}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="kg-embedding-profile" className="text-xs font-medium text-[var(--foreground)]">
              Embedding model
            </Label>
            <Select value={selectedEmbeddingProfileId} onValueChange={setSelectedEmbeddingProfileId}>
              <SelectTrigger id="kg-embedding-profile" className={selectTriggerClassName}>
                <SelectValue placeholder="Select embedding model" />
              </SelectTrigger>
              <SelectContent className="rounded-xl border-[var(--border)] shadow-none">
                {embeddingProfiles.map((profile) => (
                  <SelectItem key={profile.id} value={profile.id}>
                    {embeddingProfileLabel(profile)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs leading-4 text-[var(--muted-foreground)]">
              Locked after creation. All documents in a domain share one embedding space.
            </p>
          </div>
          <div className="space-y-2 rounded-xl border border-[var(--border)] bg-[var(--background)] p-3">
            <p className="text-xs font-medium text-[var(--foreground)]">Retrieval defaults</p>
            <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="kg-top-k" className="text-xs text-[var(--foreground)]">
                  Top K Results
                </Label>
                <Input
                  id="kg-top-k"
                  type="number"
                  min={1}
                  value={newTopK}
                  onChange={(event) => setNewTopK(event.target.value)}
                  className={retrievalDefaultsInputClassName}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="kg-chunk-top-k" className="text-xs text-[var(--foreground)]">
                  Chunk Top K
                </Label>
                <Input
                  id="kg-chunk-top-k"
                  type="number"
                  min={1}
                  value={newChunkTopK}
                  onChange={(event) => setNewChunkTopK(event.target.value)}
                  className={retrievalDefaultsInputClassName}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="kg-rerank-top-k" className="text-xs text-[var(--foreground)]">
                  Rerank Top K
                </Label>
                <Input
                  id="kg-rerank-top-k"
                  type="number"
                  min={1}
                  value={newChunkRerankTopK}
                  onChange={(event) => setNewChunkRerankTopK(event.target.value)}
                  className={retrievalDefaultsInputClassName}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="kg-text-unit-tokens" className="text-xs text-[var(--foreground)]">
                  Text Unit Tokens
                </Label>
                <Input
                  id="kg-text-unit-tokens"
                  type="number"
                  min={1}
                  value={newTextUnitTokens}
                  onChange={(event) => setNewTextUnitTokens(event.target.value)}
                  className={retrievalDefaultsInputClassName}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="kg-global-tokens" className="text-xs text-[var(--foreground)]">
                  Global Tokens
                </Label>
                <Input
                  id="kg-global-tokens"
                  type="number"
                  min={1}
                  value={newGlobalTokens}
                  onChange={(event) => setNewGlobalTokens(event.target.value)}
                  className={retrievalDefaultsInputClassName}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="kg-local-tokens" className="text-xs text-[var(--foreground)]">
                  Local Tokens
                </Label>
                <Input
                  id="kg-local-tokens"
                  type="number"
                  min={1}
                  value={newLocalTokens}
                  onChange={(event) => setNewLocalTokens(event.target.value)}
                  className={retrievalDefaultsInputClassName}
                />
              </div>
            </div>
          </div>
        </div>
        <div className="mt-3 flex items-center justify-between gap-3">
          <p className="max-w-md text-xs leading-4 text-[var(--muted-foreground)]">
            Leave host port blank to auto-assign the next available configured port starting at 9621.
          </p>
          <Button type="submit" disabled={createBusy} className={`${pillButtonClassName} px-5`}>
            {createBusy ? "Creating..." : "Create"}
          </Button>
        </div>
      </form>

      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-medium text-[var(--foreground)]">Knowledge graph domains</p>
        <Button variant="outline" size="sm" onClick={() => void loadDomains()} disabled={loading} className={`${pillButtonClassName} px-4`}>
          <RefreshCw className={`mr-2 size-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {error ? <p className="text-sm text-destructive">{error}</p> : null}

      <div className="space-y-2">
        {loading ? (
          <div className="rounded-xl border border-[var(--border)] bg-[var(--background)] p-4 text-sm text-[var(--muted-foreground)]">
            Loading domains...
          </div>
        ) : domains.length === 0 ? (
          <div className="rounded-xl border border-[var(--border)] bg-[var(--background)] p-4 text-sm text-[var(--muted-foreground)]">
            No domains yet.
          </div>
        ) : (
          domains.map((domain) => {
            const busyAction = actionBusyByDomain[domain.id];
            const statusLabel = domain.status || (domain.is_healthy ? "running" : "unknown");
            return (
              <div key={domain.id} className="rounded-xl border border-[var(--border)] bg-[var(--background)] p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="text-sm font-medium text-[var(--foreground)]">{domain.display_name || domain.id}</p>
                    <p className="text-xs text-[var(--muted-foreground)]">
                      {domain.id} - port {domain.host_port} - {statusLabel}
                    </p>
                    <p className="text-xs text-[var(--muted-foreground)]">
                      Embedding:{" "}
                      {domain.embedding
                        ? `${domain.embedding.model}${domain.embedding.dimensions ? ` · ${domain.embedding.dimensions} dims` : ""} · locked`
                        : "Legacy / unknown"}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    <Button size="sm" variant="outline" disabled={Boolean(busyAction)} onClick={() => void runAction(domain.id, "up")} className={pillButtonClassName}>
                      {busyAction === "up" ? "Starting..." : "Start"}
                    </Button>
                    <Button size="sm" variant="outline" disabled={Boolean(busyAction)} onClick={() => void runAction(domain.id, "down")} className={pillButtonClassName}>
                      {busyAction === "down" ? "Stopping..." : "Stop"}
                    </Button>
                    <Button size="sm" variant="outline" disabled={Boolean(busyAction)} onClick={() => void runAction(domain.id, "recreate")} className={pillButtonClassName}>
                      {busyAction === "recreate" ? "Recreating..." : "Recreate"}
                    </Button>
                    <Button size="sm" variant="outline" disabled={Boolean(busyAction)} onClick={() => void runAction(domain.id, "regenerate")} className={pillButtonClassName}>
                      {busyAction === "regenerate" ? "Regenerating..." : "Regenerate"}
                    </Button>
                    <Button size="sm" variant="destructive" disabled={Boolean(busyAction)} onClick={() => void runAction(domain.id, "archive")} className={pillButtonClassName}>
                      {busyAction === "archive" ? "Archiving..." : "Archive"}
                    </Button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
