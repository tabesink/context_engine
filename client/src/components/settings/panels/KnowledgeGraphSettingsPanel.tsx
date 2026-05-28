"use client";

import * as React from "react";
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
import { Button } from "@/components/ui/button";
import { adminDocumentsApi, type AdminAuditLog, type AdminDocument } from "@/lib/api/admin-documents";
import { aiSettingsApi } from "@/lib/api/ai-settings";
import { APIError } from "@/lib/api/client";
import {
  knowledgeGraphAdminApi,
  type CreateKnowledgeGraphDomainPayload,
  type KnowledgeGraphDomain,
} from "@/lib/api/knowledge-graph-admin";
import { CreateDomainForm } from "@/components/settings/lightrag-domains/CreateDomainForm";
import { DomainLifecycleCard } from "@/components/settings/lightrag-domains/DomainLifecycleCard";
import { DomainOverviewCards } from "@/components/settings/lightrag-domains/DomainOverviewCards";
import { useRegisterLightragDomainsActions } from "@/components/settings/settings-panel-actions";
import { SectionCard } from "@/components/surfaces/SectionCard";
import { PanelState } from "@/components/surfaces/PanelState";
import { settingsPanelContentClassName } from "@/components/settings/settings-controls";
import { useRunningDomainsProcessingStatus } from "@/hooks/use-running-domains-processing-status";
import { selectIsAdmin, useAuthStore } from "@/stores/auth-store";
import type { AIModelProfile } from "@/types/ai-settings";

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof APIError) {
    const body = error.body as { detail?: unknown } | null;
    if (typeof body?.detail === "string") return body.detail;
    if (body?.detail && typeof body.detail === "object" && "message" in body.detail) {
      const message = (body.detail as { message?: unknown }).message;
      if (typeof message === "string") return message;
    }
  }
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

type DomainAction = "up" | "down" | "repair" | "archive" | "purge";
type ConfirmableAction = "archive" | "purge";

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
  const [purgePreviewByDomain, setPurgePreviewByDomain] = React.useState<
    Record<string, { document_count: number; active_jobs: number } | null>
  >({});
  const [documentsDialogDomainId, setDocumentsDialogDomainId] = React.useState<string | null>(null);
  const [logsDialogDomainId, setLogsDialogDomainId] = React.useState<string | null>(null);
  const [createBusy, setCreateBusy] = React.useState(false);
  const [createOpen, setCreateOpen] = React.useState(false);
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
    await Promise.all([loadDomains(), loadDocuments(), loadAuditLogs()]);
  }, [loadDomains, loadDocuments, loadAuditLogs]);

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
        // Create flow surfaces API errors on submit.
      }
    }, 0);
    return () => window.clearTimeout(task);
  }, [isAdmin]);

  const headerActions = React.useMemo(
    () => ({
      onRefresh: () => void refreshAll(),
      onToggleCreate: () => setCreateOpen((open) => !open),
      createOpen,
      loading: loading || documentsLoading,
    }),
    [createOpen, documentsLoading, loading, refreshAll],
  );

  useRegisterLightragDomainsActions(isAdmin ? headerActions : null);

  const { statusByDomain } = useRunningDomainsProcessingStatus(domains, isAdmin);

  const runAction = async (domainId: string, action: DomainAction) => {
    setActionBusyByDomain((prev) => ({ ...prev, [domainId]: action }));
    setError(null);
    setNotice(null);
    try {
      if (action === "up") await knowledgeGraphAdminApi.up(domainId);
      if (action === "down") await knowledgeGraphAdminApi.down(domainId);
      if (action === "repair") await knowledgeGraphAdminApi.repair(domainId);
      if (action === "archive") await knowledgeGraphAdminApi.remove(domainId);
      if (action === "purge") {
        if (!purgePreviewByDomain[domainId]) {
          throw new Error("Run Preview Purge before purging permanently.");
        }
        await knowledgeGraphAdminApi.purge(domainId);
        setPurgePreviewByDomain((prev) => ({ ...prev, [domainId]: null }));
      }
      if (action === "repair") setNotice(`Repaired domain ${domainId}`);
      await refreshAll();
    } catch (nextError) {
      setError(getErrorMessage(nextError, `Failed to ${action} domain`));
    } finally {
      setActionBusyByDomain((prev) => ({ ...prev, [domainId]: null }));
    }
  };

  const runPreviewPurge = async (domainId: string) => {
    setActionBusyByDomain((prev) => ({ ...prev, [domainId]: "purge" }));
    setError(null);
    setNotice(null);
    try {
      const preview = await knowledgeGraphAdminApi.purgePreview(domainId);
      setPurgePreviewByDomain((prev) => ({
        ...prev,
        [domainId]: {
          document_count: preview.document_count,
          active_jobs: preview.active_jobs,
        },
      }));
      setNotice(`Preview for ${domainId}: ${preview.document_count} docs, ${preview.active_jobs} active jobs.`);
    } catch (nextError) {
      setError(getErrorMessage(nextError, `Failed to preview purge for ${domainId}`));
    } finally {
      setActionBusyByDomain((prev) => ({ ...prev, [domainId]: null }));
    }
  };

  const runAdvancedAction = async (domainId: string, action: "recreate" | "regenerate") => {
    setActionBusyByDomain((prev) => ({ ...prev, [domainId]: "repair" }));
    setError(null);
    setNotice(null);
    try {
      if (action === "recreate") await knowledgeGraphAdminApi.recreate(domainId);
      if (action === "regenerate") await knowledgeGraphAdminApi.regenerate(domainId);
      setNotice(`${action === "recreate" ? "Recreated container for" : "Regenerated config for"} ${domainId}`);
      await refreshAll();
    } catch (nextError) {
      setError(getErrorMessage(nextError, `Failed to ${action} for ${domainId}`));
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

  const onCreate = async (payload: {
    domainId: string;
    displayName: string;
    hostPort?: number;
    topK: number;
    chunkTopK: number;
    chunkRerankTopK: number;
    textUnitTokens: number;
    globalTokens: number;
    localTokens: number;
  }) => {
    if (!selectedEmbeddingProfileId) {
      setError("Select an embedding model before creating a domain");
      return;
    }
    if (payload.hostPort !== undefined && (payload.hostPort < 1 || payload.hostPort > 65535)) {
      setError("Host port must be an integer between 1 and 65535");
      return;
    }

    setCreateBusy(true);
    setError(null);
    setNotice(null);
    const createPayload: CreateKnowledgeGraphDomainPayload = {
      domain_id: payload.domainId,
      display_name: payload.displayName || undefined,
      host_port: payload.hostPort,
      embedding_profile_id: selectedEmbeddingProfileId,
      start: true,
      top_k: payload.topK,
      chunk_top_k: payload.chunkTopK,
      chunk_rerank_top_k: payload.chunkRerankTopK,
      max_token_for_text_unit: payload.textUnitTokens,
      max_token_for_global_context: payload.globalTokens,
      max_token_for_local_context: payload.localTokens,
    };
    try {
      await knowledgeGraphAdminApi.create(createPayload);
      setCreateOpen(false);
      setNotice(`Created and started domain ${payload.domainId}`);
      await refreshAll();
    } catch (nextError) {
      setError(getErrorMessage(nextError, "Failed to create domain"));
      throw nextError;
    } finally {
      setCreateBusy(false);
    }
  };

  const activeDocuments = React.useMemo(() => documents.filter((doc) => doc.status !== "deleted"), [documents]);

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

  const logsByDomainId = React.useMemo(() => {
    const grouped = new Map<string, AdminAuditLog[]>();
    for (const row of auditLogs) {
      const domainId =
        row.target_id ??
        (row.metadata && typeof row.metadata === "object"
          ? ((row.metadata as Record<string, unknown>).domain_id as string | undefined)
          : undefined);
      if (!domainId) continue;
      const existing = grouped.get(domainId) ?? [];
      existing.push(row);
      grouped.set(domainId, existing);
    }
    return grouped;
  }, [auditLogs]);

  const domainDocuments = documentsDialogDomainId ? (documentsByDomainId.get(documentsDialogDomainId) ?? []) : [];

  const domainLogs = React.useMemo(() => {
    if (!logsDialogDomainId) return [];
    return logsByDomainId.get(logsDialogDomainId) ?? [];
  }, [logsByDomainId, logsDialogDomainId]);

  const confirmActionLabel = confirmAction?.action ?? null;

  const onConfirmAction = async () => {
    if (!confirmAction) return;
    const { domainId, action } = confirmAction;
    if (action === "purge" && !purgePreviewByDomain[domainId]) {
      setConfirmAction(null);
      setError("Run Preview Purge before purging permanently.");
      return;
    }
    setConfirmAction(null);
    await runAction(domainId, action);
  };

  if (!isAdmin) {
    return (
      <SectionCard title="Admin access required" description="Sign in with an admin account to manage knowledge graph domains.">
        <div className="h-1" />
      </SectionCard>
    );
  }

  return (
    <div className={settingsPanelContentClassName}>
      <CreateDomainForm
        open={createOpen}
        createBusy={createBusy}
        embeddingProfiles={embeddingProfiles}
        selectedEmbeddingProfileId={selectedEmbeddingProfileId}
        onSelectedEmbeddingProfileIdChange={setSelectedEmbeddingProfileId}
        onCancel={() => {
          setCreateOpen(false);
          setError(null);
        }}
        onSubmit={onCreate}
      />

      {error ? <p className="text-sm text-destructive">{error}</p> : null}
      {notice ? <p className="text-sm text-muted-foreground">{notice}</p> : null}

      <input ref={uploadInputRef} type="file" className="hidden" onChange={onUploadFileSelected} />

      {loading ? (
        <PanelState title="Loading domains..." />
      ) : domains.length === 0 ? (
        <PanelState title="No domains yet." />
      ) : (
        <SectionCard className="space-y-4">
          <DomainOverviewCards domains={domains} documentsByDomainId={documentsByDomainId} />
          <div className="space-y-4">
            {domains.map((domain) => (
              <DomainLifecycleCard
                key={domain.id}
                domain={domain}
                documents={documentsByDomainId.get(domain.id) ?? []}
                logs={logsByDomainId.get(domain.id) ?? []}
                processingStatus={statusByDomain.get(domain.id)}
                busyAction={actionBusyByDomain[domain.id]}
                uploadBusy={Boolean(uploadBusyByDomain[domain.id])}
                onRunAction={(domainId, action) => void runAction(domainId, action)}
                onRunAdvancedAction={(domainId, action) => void runAdvancedAction(domainId, action)}
                onUpload={triggerUpload}
                onOpenDocuments={setDocumentsDialogDomainId}
                onOpenLogs={setLogsDialogDomainId}
                onArchive={(domainId) => setConfirmAction({ domainId, action: "archive" })}
                onPreviewPurge={(domainId) => void runPreviewPurge(domainId)}
                onPurge={(domainId) => setConfirmAction({ domainId, action: "purge" })}
              />
            ))}
          </div>
        </SectionCard>
      )}

      <Dialog open={Boolean(documentsDialogDomainId)} onOpenChange={(open) => !open && setDocumentsDialogDomainId(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Domain documents</DialogTitle>
            <DialogDescription>
              {documentsDialogDomainId ? `Documents uploaded to ${documentsDialogDomainId}` : "Documents for selected domain"}
            </DialogDescription>
          </DialogHeader>
          <div className="max-h-[360px] overflow-y-auto rounded-md border border-border">
            {documentsLoading ? (
              <p className="p-3 text-xs text-muted-foreground">Loading documents...</p>
            ) : domainDocuments.length === 0 ? (
              <p className="p-3 text-xs text-muted-foreground">No uploaded documents in this domain.</p>
            ) : (
              <div className="divide-y divide-border">
                {domainDocuments.map((doc) => (
                  <div key={doc.id} className="p-3">
                    <p className="text-sm text-foreground">{doc.filename}</p>
                    <p className="text-xs text-muted-foreground">
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
          <div className="max-h-[360px] overflow-y-auto rounded-md border border-border">
            {logsLoading ? (
              <p className="p-3 text-xs text-muted-foreground">Loading logs...</p>
            ) : domainLogs.length === 0 ? (
              <p className="p-3 text-xs text-muted-foreground">No logs for this domain yet.</p>
            ) : (
              <div className="divide-y divide-border">
                {domainLogs.map((row) => (
                  <div key={row.id} className="p-3">
                    <p className="text-sm text-foreground">{row.event}</p>
                    <p className="text-xs text-muted-foreground">{formatDateLabel(row.created_at)}</p>
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
              {confirmActionLabel === "purge"
                ? "Purge this domain permanently? This cannot be undone. Run Preview Purge first."
                : null}
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

function formatDateLabel(value: string): string {
  const timestamp = Date.parse(value);
  if (Number.isNaN(timestamp)) return value;
  return new Date(timestamp).toLocaleString();
}
