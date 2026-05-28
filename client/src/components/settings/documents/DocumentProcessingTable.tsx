import { ChevronRight, FileText } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import type { AdminDomainDocumentsProcessingStatus } from "@/api/processing-status";
import { DocumentFailureDetails } from "@/components/settings/documents/DocumentFailureDetails";
import { DocumentRetryAction } from "@/components/settings/documents/DocumentRetryAction";
import { DocumentStatusChip } from "@/components/settings/documents/DocumentStatusChip";
import { PanelState } from "@/components/surfaces/PanelState";

type Row = AdminDomainDocumentsProcessingStatus["documents"][number];

function stageLabel(status: Row["status"]) {
  if (status === "queued") return "Queued";
  if (status === "uploaded") return "Upload";
  if (status === "indexing") return "Graph/Index";
  if (status === "ready") return "Indexed";
  if (status === "failed") return "Failed";
  if (status === "deleted") return "Deleted";
  return "Unknown";
}

function statusDotClassName(status: Row["status"]) {
  if (status === "ready") return "bg-emerald-500";
  if (status === "failed") return "bg-destructive";
  if (status === "queued" || status === "indexing" || status === "uploaded") return "bg-amber-500";
  return "bg-muted-foreground";
}

function formatDateLabel(value: string) {
  const ts = Date.parse(value);
  if (Number.isNaN(ts)) return value;
  return new Date(ts).toLocaleString();
}

export function DocumentProcessingTable({
  data,
  loading,
  error,
  retryBusyByDocumentId,
  onRetry,
}: {
  data: AdminDomainDocumentsProcessingStatus | null;
  loading: boolean;
  error: string | null;
  retryBusyByDocumentId: Record<string, boolean>;
  onRetry: (documentId: string) => void;
}) {
  if (error) {
    return <PanelState tone="danger" title="Failed loading processing rows" description={error} />;
  }
  if (loading && !data) {
    return (
      <div className="space-y-5 py-3">
        <Skeleton className="h-4 w-52" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-4/5" />
      </div>
    );
  }
  if (!data || data.documents.length === 0) {
    return <PanelState title="No documents in this domain yet." />;
  }

  return (
    <div role="list" aria-label="Document processing queue" className="space-y-1">
      {data.documents.map((row) => (
        <div
          key={row.document_id}
          role="listitem"
          className="group grid grid-cols-[auto_1fr_auto] items-center gap-4 rounded-lg px-0 py-4 transition-colors hover:bg-muted/25"
        >
          <span className={`mt-1 size-2 rounded-full ${statusDotClassName(row.status)}`} aria-hidden />
          <div className="min-w-0">
            <div className="flex min-w-0 items-center gap-2">
              <FileText className="size-4 shrink-0 text-muted-foreground/70" aria-hidden />
              <p className="truncate text-sm font-medium text-foreground">{row.filename}</p>
            </div>
            <p className="mt-1 truncate pl-6 text-xs text-muted-foreground">
              Domain {row.domain_id ?? data.domain_id} · {stageLabel(row.status)}
              {row.job_id ? ` · Job ${row.job_id}` : ""} · Updated {formatDateLabel(row.updated_at)}
            </p>
            {row.status === "failed" ? (
              <div className="mt-2 pl-6">
                <DocumentFailureDetails message={row.message} />
              </div>
            ) : row.message ? (
              <p className="mt-1 truncate pl-6 text-xs text-muted-foreground">{row.message}</p>
            ) : null}
          </div>
          <div className="flex min-w-[128px] items-center justify-end gap-3 text-right">
            <div className="space-y-1">
              <DocumentStatusChip status={row.status} />
              <p className="text-[11px] text-muted-foreground">Chunks - · Assets -</p>
            </div>
            <DocumentRetryAction
              canRetry={row.can_retry}
              busy={Boolean(retryBusyByDocumentId[row.document_id])}
              onRetry={() => onRetry(row.document_id)}
            />
            <ChevronRight className="size-4 text-muted-foreground/60" aria-hidden />
          </div>
        </div>
      ))}
    </div>
  );
}
