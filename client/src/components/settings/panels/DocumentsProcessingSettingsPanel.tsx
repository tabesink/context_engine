"use client";

import * as React from "react";
import {
  fetchAdminDomainDocumentsProcessingStatus,
  type AdminDomainDocumentsProcessingStatus,
} from "@/api/processing-status";
import { DocumentProcessingOverview } from "@/components/settings/documents/DocumentProcessingOverview";
import { DocumentProcessingTable } from "@/components/settings/documents/DocumentProcessingTable";
import { useAdaptivePolling } from "@/hooks/use-adaptive-polling";
import { knowledgeGraphAdminApi } from "@/lib/api/knowledge-graph-admin";
import { adminDocumentsApi } from "@/lib/api/admin-documents";
import { PanelState } from "@/components/surfaces/PanelState";
import { settingsPanelContentClassName } from "@/components/settings/settings-controls";
import { selectIsAdmin, useAuthStore } from "@/stores/auth-store";

type RowStatus = AdminDomainDocumentsProcessingStatus["documents"][number]["status"];

function isActiveStatus(status: RowStatus) {
  return status === "queued" || status === "indexing" || status === "uploaded";
}

export function getDocumentsPanelPollDelay(data: AdminDomainDocumentsProcessingStatus | null) {
  const hasActive = (data?.documents ?? []).some((item) => isActiveStatus(item.status));
  return hasActive ? 3000 : 15000;
}

export function DocumentsProcessingSettingsPanel() {
  const isAdmin = useAuthStore(selectIsAdmin);
  const [domains, setDomains] = React.useState<Array<{ id: string; display_name: string }>>([]);
  const [domainId, setDomainId] = React.useState<string>("");
  const [data, setData] = React.useState<AdminDomainDocumentsProcessingStatus | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [retryBusyByDocumentId, setRetryBusyByDocumentId] = React.useState<Record<string, boolean>>({});

  const load = React.useCallback(async () => {
    if (!domainId) return data;
    setLoading((current) => current || data === null);
    try {
      const next = await fetchAdminDomainDocumentsProcessingStatus(domainId, { limit: 100, offset: 0 });
      setData(next);
      setError(null);
      return next;
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Failed to load document processing status.");
      return data;
    } finally {
      setLoading(false);
    }
  }, [data, domainId]);

  React.useEffect(() => {
    if (!isAdmin) return;
    let cancelled = false;
    const task = window.setTimeout(async () => {
      try {
        const list = await knowledgeGraphAdminApi.list();
        if (cancelled) return;
        setDomains(list.map((item) => ({ id: item.id, display_name: item.display_name || item.id })));
        if (!domainId && list[0]) setDomainId(list[0].id);
      } catch (nextError) {
        if (cancelled) return;
        setError(nextError instanceof Error ? nextError.message : "Failed to load domains.");
      }
    }, 0);
    return () => {
      cancelled = true;
      window.clearTimeout(task);
    };
  }, [domainId, isAdmin]);

  useAdaptivePolling({
    enabled: isAdmin && Boolean(domainId),
    run: load,
    getDelay: (next) => getDocumentsPanelPollDelay(next),
    errorDelayMs: 15000,
    initialDelayMs: 0,
  });

  const onRetry = async (documentId: string) => {
    setRetryBusyByDocumentId((prev) => ({ ...prev, [documentId]: true }));
    try {
      await adminDocumentsApi.reingest(documentId);
      await load();
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Failed to queue retry.");
    } finally {
      setRetryBusyByDocumentId((prev) => ({ ...prev, [documentId]: false }));
    }
  };

  if (!isAdmin) {
    return <PanelState title="Admin access required" description="Sign in as an admin to view document processing status." />;
  }

  const counts = data?.status_counts;

  return (
    <div className={settingsPanelContentClassName}>
      <DocumentProcessingOverview domains={domains} domainId={domainId} counts={counts} onDomainChange={setDomainId} />
      <DocumentProcessingTable
        data={data}
        loading={loading}
        error={error}
        retryBusyByDocumentId={retryBusyByDocumentId}
        onRetry={(documentId) => void onRetry(documentId)}
      />
    </div>
  );
}
