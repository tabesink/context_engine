"use client";

import * as React from "react";
import { ChevronDown, Minus, MoreHorizontal, Plus, RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { adminDocumentsApi, type AdminAuditLog, type AdminDocument } from "@/lib/api/admin-documents";
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
type ConfirmableAction = "recreate" | "regenerate" | "archive";
type RetrievalProfile = "precise" | "balanced" | "broad" | "custom";

const panelClassName = "rounded-xl border border-[var(--border)] bg-[var(--background)] p-4";
const inputClassName = "h-9 rounded-full border-[var(--border)] bg-[var(--background)] shadow-none";
const selectTriggerClassName = "h-9 rounded-full border-[var(--border)] bg-[var(--background)] shadow-none";
const pillButtonClassName = "rounded-full shadow-none";
const retrievalDefaultsInputClassName = "h-9 rounded-full border-[var(--border)] bg-[var(--background)] shadow-none";

const RETRIEVAL_PROFILES: Record<Exclude<RetrievalProfile, "custom">, { topK: string; chunkTopK: string; rerankTopK: string; textTokens: string; globalTokens: string; localTokens: string }> = {
  precise: { topK: "6", chunkTopK: "6", rerankTopK: "6", textTokens: "2500", globalTokens: "2500", localTokens: "2500" },
  balanced: { topK: "10", chunkTopK: "10", rerankTopK: "10", textTokens: "4000", globalTokens: "4000", localTokens: "4000" },
  broad: { topK: "20", chunkTopK: "20", rerankTopK: "20", textTokens: "6000", globalTokens: "6000", localTokens: "6000" },
};

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
  const [documents, setDocuments] = React.useState<AdminDocument[]>([]);
  const [auditLogs, setAuditLogs] = React.useState<AdminAuditLog[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [documentsLoading, setDocumentsLoading] = React.useState(false);
  const [logsLoading, setLogsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [notice, setNotice] = React.useState<string | null>(null);
  const [actionBusyByDomain, setActionBusyByDomain] = React.useState<Record<string, DomainAction | null>>({});
  const [uploadBusyByDomain, setUploadBusyByDomain] = React.useState<Record<string, boolean>>({});
  const [confirmAction, setConfirmAction] = React.useState<{ domainId: string; action: ConfirmableAction } | null>(null);
  const [documentsDialogDomainId, setDocumentsDialogDomainId] = React.useState<string | null>(null);
  const [logsDialogDomainId, setLogsDialogDomainId] = React.useState<string | null>(null);
  const [createBusy, setCreateBusy] = React.useState(false);
  const [createOpen, setCreateOpen] = React.useState(false);
  const [newDomainId, setNewDomainId] = React.useState("");
  const [newDisplayName, setNewDisplayName] = React.useState("");
  const [useCustomHostPort, setUseCustomHostPort] = React.useState(false);
  const [retrievalProfile, setRetrievalProfile] = React.useState<RetrievalProfile>("balanced");
  const [newHostPort, setNewHostPort] = React.useState("");
  const [newTopK, setNewTopK] = React.useState("10");
  const [newChunkTopK, setNewChunkTopK] = React.useState("10");
  const [newChunkRerankTopK, setNewChunkRerankTopK] = React.useState("10");
  const [newTextUnitTokens, setNewTextUnitTokens] = React.useState("4000");
  const [newGlobalTokens, setNewGlobalTokens] = React.useState("4000");
  const [newLocalTokens, setNewLocalTokens] = React.useState("4000");
  const [embeddingProfiles, setEmbeddingProfiles] = React.useState<AIModelProfile[]>([]);
  const [selectedEmbeddingProfileId, setSelectedEmbeddingProfileId] = React.useState("");
  const [uploadTargetDomainId, setUploadTargetDomainId] = React.useState<string | null>(null);
  const uploadInputRef = React.useRef<HTMLInputElement | null>(null);

  const loadDomains = React.useCallback(async () => {
    setLoading(true);
    try {
      const list = await knowledgeGraphAdminApi.list();
      setDomains(list);
    } catch (nextError) {
      setError(getErrorMessage(nextError, "Failed to load knowledge graph domains"));
    } finally {
      setLoading(false);
    }
  }, []);

  const loadDocuments = React.useCallback(async () => {
    setDocumentsLoading(true);
    try {
      const rows = await adminDocumentsApi.list();
      setDocuments(rows);
    } catch (nextError) {
      setError(getErrorMessage(nextError, "Failed to load documents"));
    } finally {
      setDocumentsLoading(false);
    }
  }, []);

  const loadAuditLogs = React.useCallback(async () => {
    setLogsLoading(true);
    try {
      const rows = await adminDocumentsApi.listAuditLogs();
      setAuditLogs(rows);
    } catch (nextError) {
      setError(getErrorMessage(nextError, "Failed to load audit logs"));
    } finally {
      setLogsLoading(false);
    }
  }, []);

  const refreshAll = React.useCallback(async () => {
    setError(null);
    setNotice(null);
    await Promise.all([loadDomains(), loadDocuments()]);
  }, [loadDomains, loadDocuments]);

  React.useEffect(() => {
    if (!isAdmin) return;
    const task = window.setTimeout(() => {
      void refreshAll();
    }, 0);
    return () => window.clearTimeout(task);
  }, [isAdmin, refreshAll]);

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

  React.useEffect(() => {
    if (!logsDialogDomainId || auditLogs.length > 0) return;
    void loadAuditLogs();
  }, [auditLogs.length, loadAuditLogs, logsDialogDomainId]);

  const applyProfileDefaults = (profile: Exclude<RetrievalProfile, "custom">) => {
    const defaults = RETRIEVAL_PROFILES[profile];
    setNewTopK(defaults.topK);
    setNewChunkTopK(defaults.chunkTopK);
    setNewChunkRerankTopK(defaults.rerankTopK);
    setNewTextUnitTokens(defaults.textTokens);
    setNewGlobalTokens(defaults.globalTokens);
    setNewLocalTokens(defaults.localTokens);
  };

  const runAction = async (domainId: string, action: DomainAction) => {
    setActionBusyByDomain((prev) => ({ ...prev, [domainId]: action }));
    setError(null);
    setNotice(null);
    try {
      if (action === "up") await knowledgeGraphAdminApi.up(domainId);
      if (action === "down") await knowledgeGraphAdminApi.down(domainId);
      if (action === "recreate") await knowledgeGraphAdminApi.recreate(domainId);
      if (action === "regenerate") await knowledgeGraphAdminApi.regenerate(domainId);
      if (action === "archive") await knowledgeGraphAdminApi.remove(domainId);
      await refreshAll();
    } catch (nextError) {
      setError(getErrorMessage(nextError, `Failed to ${action} domain`));
    } finally {
      setActionBusyByDomain((prev) => ({ ...prev, [domainId]: null }));
    }
  };

  const runRestart = async (domainId: string) => {
    setActionBusyByDomain((prev) => ({ ...prev, [domainId]: "down" }));
    setError(null);
    setNotice(null);
    try {
      await knowledgeGraphAdminApi.down(domainId);
      await knowledgeGraphAdminApi.up(domainId);
      setNotice(`Restarted domain ${domainId}`);
      await refreshAll();
    } catch (nextError) {
      setError(getErrorMessage(nextError, `Failed to restart domain ${domainId}`));
    } finally {
      setActionBusyByDomain((prev) => ({ ...prev, [domainId]: null }));
    }
  };

  const triggerUpload = (domainId: string) => {
    setUploadTargetDomainId(domainId);
    uploadInputRef.current?.click();
  };

  const onUploadFileSelected = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    const domainId = uploadTargetDomainId;
    event.target.value = "";
    if (!file || !domainId) return;
    setUploadBusyByDomain((prev) => ({ ...prev, [domainId]: true }));
    setError(null);
    setNotice(null);
    try {
      await adminDocumentsApi.uploadToDomain(file, domainId);
      setNotice(`Uploaded ${file.name} to ${domainId}`);
      await refreshAll();
    } catch (nextError) {
      setError(getErrorMessage(nextError, "Failed to upload document"));
    } finally {
      setUploadBusyByDomain((prev) => ({ ...prev, [domainId]: false }));
      setUploadTargetDomainId(null);
    }
  };

  const openDocumentsDialog = (domainId: string) => {
    setDocumentsDialogDomainId(domainId);
  };

  const openLogsDialog = (domainId: string) => {
    setLogsDialogDomainId(domainId);
  };

  const onCreate = async (event: React.FormEvent) => {
    event.preventDefault();
    const domainId = newDomainId.trim();
    const displayName = newDisplayName.trim();
    const hostPortRaw = useCustomHostPort ? newHostPort.trim() : "";
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
    setNotice(null);
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
      setUseCustomHostPort(false);
      setNewHostPort("");
      setRetrievalProfile("balanced");
      applyProfileDefaults("balanced");
      setCreateOpen(false);
      setNotice(`Created domain ${domainId}`);
      await refreshAll();
    } catch (nextError) {
      setError(getErrorMessage(nextError, "Failed to create domain"));
    } finally {
      setCreateBusy(false);
    }
  };

  const activeDocuments = React.useMemo(() => {
    return documents.filter((doc) => doc.status !== "deleted");
  }, [documents]);

  const documentsByDomainId = React.useMemo(() => {
    const grouped = new Map<string, AdminDocument[]>();
    for (const document of activeDocuments) {
      const lightrag = document.metadata?.lightrag;
      if (!lightrag || typeof lightrag !== "object") continue;
      const domainIdRaw = (lightrag as Record<string, unknown>).domain_id ?? (lightrag as Record<string, unknown>).domain;
      if (typeof domainIdRaw !== "string" || !domainIdRaw) continue;
      const existing = grouped.get(domainIdRaw) ?? [];
      existing.push(document);
      grouped.set(domainIdRaw, existing);
    }
    return grouped;
  }, [activeDocuments]);

  const domainDocuments = documentsDialogDomainId ? documentsByDomainId.get(documentsDialogDomainId) ?? [] : [];

  const domainLogs = React.useMemo(() => {
    if (!logsDialogDomainId) return [];
    return auditLogs.filter((row) => {
      if (row.target_id === logsDialogDomainId) return true;
      const metadata = row.metadata;
      if (!metadata || typeof metadata !== "object") return false;
      const domainId = (metadata as Record<string, unknown>).domain_id;
      return domainId === logsDialogDomainId;
    });
  }, [auditLogs, logsDialogDomainId]);

  const confirmActionLabel = confirmAction?.action ?? null;

  const onConfirmAction = async () => {
    if (!confirmAction) return;
    const { domainId, action } = confirmAction;
    setConfirmAction(null);
    await runAction(domainId, action);
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
      <div className="space-y-1">
        <p className="text-sm font-medium text-[var(--foreground)]">Knowledge Graph</p>
        <p className="text-xs text-[var(--muted-foreground)]">Manage retrieval domains, document uploads, and lifecycle actions.</p>
      </div>

      <div className="flex items-center justify-between gap-3">
        <Button variant="outline" size="sm" onClick={() => setCreateOpen((open) => !open)} className={`${pillButtonClassName} px-4`}>
          {createOpen ? <Minus className="mr-2 size-3.5" /> : <Plus className="mr-2 size-3.5" />}
          {createOpen ? "Hide create form" : "Create domain"}
        </Button>
        <Button variant="outline" size="sm" onClick={() => void refreshAll()} disabled={loading || documentsLoading} className={`${pillButtonClassName} px-4`}>
          <RefreshCw className={`mr-2 size-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {createOpen ? (
        <form onSubmit={onCreate} className={panelClassName}>
          <p className="text-sm font-medium text-[var(--foreground)]">Create knowledge graph domain</p>
          <p className="mt-1 text-xs leading-5 text-[var(--muted-foreground)]">
            Create an isolated retrieval domain for documents and evidence.
          </p>

          <div className="mt-4 space-y-4">
            <div>
              <p className="mb-2 text-xs font-medium text-[var(--foreground)]">Domain identity</p>
              <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
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
              </div>
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
                Locked after creation. All documents in this domain share the same embedding space.
              </p>
            </div>

            <div className="space-y-2.5">
              <p className="text-xs font-medium text-[var(--foreground)]">Host port</p>
              <p className="text-xs leading-4 text-[var(--muted-foreground)]">Choose automatic assignment or provide a fixed port.</p>
              <div className="space-y-2" role="radiogroup" aria-label="Host port mode">
                <label className="flex items-center gap-2 text-xs text-[var(--foreground)]">
                  <input
                    type="radio"
                    name="host-port-mode"
                    checked={!useCustomHostPort}
                    onChange={() => {
                      setUseCustomHostPort(false);
                      setNewHostPort("");
                    }}
                  />
                  <span>Auto-assign available port</span>
                </label>
                <label className="flex items-center gap-2 text-xs text-[var(--foreground)]">
                  <input type="radio" name="host-port-mode" checked={useCustomHostPort} onChange={() => setUseCustomHostPort(true)} />
                  <span>Use custom port</span>
                </label>
              </div>
              {useCustomHostPort ? (
                <div className="space-y-1.5">
                  <Label htmlFor="kg-host-port" className="text-xs font-medium text-[var(--foreground)]">
                    Custom port
                  </Label>
                  <Input
                    id="kg-host-port"
                    type="number"
                    min={1}
                    max={65535}
                    placeholder="9621"
                    value={newHostPort}
                    onChange={(event) => setNewHostPort(event.target.value)}
                    className={inputClassName}
                  />
                </div>
              ) : null}
            </div>

            <details className="group space-y-2 pt-1">
              <summary className="flex cursor-pointer list-none items-center justify-between text-xs font-medium text-[var(--foreground)]">
                <span>Advanced retrieval defaults</span>
                <ChevronDown className="size-3.5 text-[var(--muted-foreground)] group-open:rotate-180" />
              </summary>
              <p className="text-xs leading-4 text-[var(--muted-foreground)]">Tune recall and token budgets used when this domain is created.</p>
              <div className="space-y-3">
                <div className="space-y-1.5">
                  <Label htmlFor="kg-retrieval-profile" className="text-xs text-[var(--foreground)]">
                    Retrieval profile
                  </Label>
                  <Select
                    value={retrievalProfile}
                    onValueChange={(value) => {
                      const profile = value as RetrievalProfile;
                      setRetrievalProfile(profile);
                      if (profile !== "custom") applyProfileDefaults(profile);
                    }}
                  >
                    <SelectTrigger id="kg-retrieval-profile" className={selectTriggerClassName}>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="rounded-xl border-[var(--border)] shadow-none">
                      <SelectItem value="precise">Precise</SelectItem>
                      <SelectItem value="balanced">Balanced</SelectItem>
                      <SelectItem value="broad">Broad</SelectItem>
                      <SelectItem value="custom">Custom</SelectItem>
                    </SelectContent>
                  </Select>
                  {retrievalProfile === "precise" ? (
                    <p className="text-xs text-[var(--muted-foreground)]">Fewer, higher-confidence chunks.</p>
                  ) : null}
                  {retrievalProfile === "balanced" ? (
                    <p className="text-xs text-[var(--muted-foreground)]">Recommended default for most workloads.</p>
                  ) : null}
                  {retrievalProfile === "broad" ? (
                    <p className="text-xs text-[var(--muted-foreground)]">More recall for exploratory questions.</p>
                  ) : null}
                </div>
                {retrievalProfile === "custom" ? (
                  <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
                    <NumberInput id="kg-top-k" label="Top K Results" value={newTopK} onChange={setNewTopK} />
                    <NumberInput id="kg-chunk-top-k" label="Chunk Top K" value={newChunkTopK} onChange={setNewChunkTopK} />
                    <NumberInput id="kg-rerank-top-k" label="Rerank Top K" value={newChunkRerankTopK} onChange={setNewChunkRerankTopK} />
                    <NumberInput id="kg-text-unit-tokens" label="Text Unit Tokens" value={newTextUnitTokens} onChange={setNewTextUnitTokens} />
                    <NumberInput id="kg-global-tokens" label="Global Tokens" value={newGlobalTokens} onChange={setNewGlobalTokens} />
                    <NumberInput id="kg-local-tokens" label="Local Tokens" value={newLocalTokens} onChange={setNewLocalTokens} />
                  </div>
                ) : null}
              </div>
            </details>
          </div>

          <div className="mt-4 flex items-center justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              className={pillButtonClassName}
              onClick={() => {
                setCreateOpen(false);
                setError(null);
              }}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createBusy} className={`${pillButtonClassName} px-5`}>
              {createBusy ? "Creating..." : "Create"}
            </Button>
          </div>
        </form>
      ) : null}

      <div className="pt-1">
        <p className="text-sm font-medium text-[var(--foreground)]">Knowledge graph domains</p>
      </div>

      {error ? <p className="text-sm text-destructive">{error}</p> : null}
      {notice ? <p className="text-sm text-[var(--muted-foreground)]">{notice}</p> : null}

      <input ref={uploadInputRef} type="file" className="hidden" onChange={onUploadFileSelected} />

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
            const isRunning = statusLabel.toLowerCase() === "running" || domain.is_healthy === true;
            const domainDocs = documentsByDomainId.get(domain.id) ?? [];
            const indexingCount = domainDocs.filter((doc) => doc.status === "indexing").length;
            const uploadedCount = domainDocs.length;
            const lastUploadLabel = formatLastUploadLabel(domainDocs);
            return (
              <div key={domain.id} className="rounded-xl border border-[var(--border)] bg-[var(--background)] p-4">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-[var(--foreground)]">{domain.display_name || domain.id}</p>
                    </div>
                    <p className="text-xs text-[var(--muted-foreground)]">
                      Domain ID: {domain.id} · Port: {domain.host_port}
                    </p>
                  </div>
                  <Badge variant={isRunning ? "secondary" : "muted"} className="rounded-full">
                    ● {isRunning ? "Running" : statusLabel}
                  </Badge>
                </div>
                <div className="mt-2 space-y-2">
                    <p className="text-xs text-[var(--muted-foreground)]">
                      Embedding:{" "}
                      {domain.embedding
                        ? `${domain.embedding.model}${domain.embedding.dimensions ? ` · ${domain.embedding.dimensions} dims` : ""} · locked`
                        : "Legacy / unknown"}
                    </p>
                    <p className="text-xs text-[var(--muted-foreground)]">
                      Documents: {uploadedCount} uploaded · {indexingCount} indexing
                      {lastUploadLabel ? ` · last upload ${lastUploadLabel}` : ""}
                    </p>
                </div>
                <div className="mt-3 flex flex-wrap gap-1.5">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={Boolean(uploadBusyByDomain[domain.id])}
                    onClick={() => triggerUpload(domain.id)}
                    className={pillButtonClassName}
                  >
                    {uploadBusyByDomain[domain.id] ? "Uploading..." : "Upload document"}
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => openDocumentsDialog(domain.id)} className={pillButtonClassName}>
                    View documents
                  </Button>
                  {isRunning ? (
                    <Button size="sm" variant="outline" disabled={Boolean(busyAction)} onClick={() => void runAction(domain.id, "down")} className={pillButtonClassName}>
                      {busyAction === "down" ? "Stopping..." : "Stop"}
                    </Button>
                  ) : (
                    <Button size="sm" variant="outline" disabled={Boolean(busyAction)} onClick={() => void runAction(domain.id, "up")} className={pillButtonClassName}>
                      {busyAction === "up" ? "Starting..." : "Start"}
                    </Button>
                  )}
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button size="sm" variant="outline" className={pillButtonClassName}>
                        More
                        <MoreHorizontal className="ml-1 size-3.5" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-52">
                      <DropdownMenuItem onSelect={() => openLogsDialog(domain.id)}>View logs</DropdownMenuItem>
                      <DropdownMenuItem disabled={!isRunning || Boolean(busyAction)} onSelect={() => void runAction(domain.id, "down")}>
                        Stop domain
                      </DropdownMenuItem>
                      <DropdownMenuItem disabled={Boolean(busyAction)} onSelect={() => void runRestart(domain.id)}>
                        Restart domain
                      </DropdownMenuItem>
                      <DropdownMenuItem disabled={Boolean(busyAction)} onSelect={() => setConfirmAction({ domainId: domain.id, action: "recreate" })}>
                        Recreate container
                      </DropdownMenuItem>
                      <DropdownMenuItem disabled={Boolean(busyAction)} onSelect={() => setConfirmAction({ domainId: domain.id, action: "regenerate" })}>
                        Regenerate indexes
                      </DropdownMenuItem>
                      <DropdownMenuItem disabled={Boolean(busyAction)} onSelect={() => setConfirmAction({ domainId: domain.id, action: "archive" })}>
                        Archive domain
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            );
          })
        )}
      </div>

      <Dialog open={Boolean(documentsDialogDomainId)} onOpenChange={(open) => !open && setDocumentsDialogDomainId(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Domain documents</DialogTitle>
            <DialogDescription>
              {documentsDialogDomainId ? `Documents uploaded to ${documentsDialogDomainId}` : "Documents for selected domain"}
            </DialogDescription>
          </DialogHeader>
          <div className="max-h-[360px] overflow-y-auto rounded-md border border-[var(--border)]">
            {documentsLoading ? (
              <p className="p-3 text-xs text-[var(--muted-foreground)]">Loading documents...</p>
            ) : domainDocuments.length === 0 ? (
              <p className="p-3 text-xs text-[var(--muted-foreground)]">No uploaded documents in this domain.</p>
            ) : (
              <div className="divide-y divide-[var(--border)]">
                {domainDocuments.map((doc) => (
                  <div key={doc.id} className="p-3">
                    <p className="text-sm text-[var(--foreground)]">{doc.filename}</p>
                    <p className="text-xs text-[var(--muted-foreground)]">
                      {doc.status} · uploaded {formatDateLabel(doc.created_at)}
                    </p>
                    {doc.status === "failed" && doc.error_message ? (
                      <p className="mt-1 text-xs text-rose-300">{doc.error_message}</p>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDocumentsDialogDomainId(null)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={Boolean(logsDialogDomainId)} onOpenChange={(open) => !open && setLogsDialogDomainId(null)}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Domain logs</DialogTitle>
            <DialogDescription>
              {logsDialogDomainId ? `Audit logs for ${logsDialogDomainId}` : "Domain audit logs"}
            </DialogDescription>
          </DialogHeader>
          <div className="max-h-[360px] overflow-y-auto rounded-md border border-[var(--border)]">
            {logsLoading ? (
              <p className="p-3 text-xs text-[var(--muted-foreground)]">Loading logs...</p>
            ) : domainLogs.length === 0 ? (
              <p className="p-3 text-xs text-[var(--muted-foreground)]">No logs for this domain yet.</p>
            ) : (
              <div className="divide-y divide-[var(--border)]">
                {domainLogs.map((row) => (
                  <div key={row.id} className="p-3">
                    <p className="text-sm text-[var(--foreground)]">{row.event}</p>
                    <p className="text-xs text-[var(--muted-foreground)]">{formatDateLabel(row.created_at)}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setLogsDialogDomainId(null)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={Boolean(confirmAction)} onOpenChange={(open) => !open && setConfirmAction(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirm action</AlertDialogTitle>
            <AlertDialogDescription>
              {confirmActionLabel === "archive" ? "Archive this domain?" : null}
              {confirmActionLabel === "recreate" ? "Recreate this domain container?" : null}
              {confirmActionLabel === "regenerate" ? "Regenerate indexes for this domain?" : null}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={() => void onConfirmAction()}>Continue</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

function NumberInput({ id, label, value, onChange }: { id: string; label: string; value: string; onChange: (value: string) => void }) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id} className="text-xs text-[var(--foreground)]">
        {label}
      </Label>
      <Input id={id} type="number" min={1} value={value} onChange={(event) => onChange(event.target.value)} className={retrievalDefaultsInputClassName} />
    </div>
  );
}

function formatDateLabel(value: string): string {
  const timestamp = Date.parse(value);
  if (Number.isNaN(timestamp)) return value;
  return new Date(timestamp).toLocaleString();
}

function formatLastUploadLabel(documents: AdminDocument[]): string | null {
  if (!documents.length) return null;
  let newestTimestamp = 0;
  for (const doc of documents) {
    const ts = Date.parse(doc.created_at);
    if (!Number.isNaN(ts) && ts > newestTimestamp) newestTimestamp = ts;
  }
  if (!newestTimestamp) return null;
  const elapsedMs = Date.now() - newestTimestamp;
  if (elapsedMs < 60_000) return "just now";
  const mins = Math.floor(elapsedMs / 60_000);
  if (mins < 60) return `${mins} min ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} hr ago`;
  const days = Math.floor(hours / 24);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}
