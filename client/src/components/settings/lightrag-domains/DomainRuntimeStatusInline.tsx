import type { DomainProcessingStatus } from "@/api/processing-status";
import type { KnowledgeGraphDomain } from "@/lib/api/knowledge-graph-admin";

export function DomainRuntimeStatusInline({
  domain,
  status,
}: {
  domain: KnowledgeGraphDomain;
  status: DomainProcessingStatus | null | undefined;
}) {
  const statusLabel = domain.status || (domain.is_healthy ? "running" : "unknown");
  const isRunning = statusLabel.toLowerCase() === "running" || domain.is_healthy === true;
  const activeMessage = status?.active?.message ? ` · ${status.active.message}` : "";

  return (
    <div className="space-y-2">
      <div className="space-y-0.5">
        <p className="text-sm font-medium text-foreground">Runtime status</p>
        <p className="text-xs text-muted-foreground">
          Port {domain.host_port} · Domain {domain.id}
        </p>
      </div>
      {status ? (
        <p className="text-xs leading-5 text-muted-foreground">
          {status.is_stale ? "Status stale" : "Live"} · Processing {status.state} · Queued {status.counts.queued} ·
          Indexing {status.counts.indexing} · Ready {status.counts.ready} · Failed {status.counts.failed}
          {activeMessage}
        </p>
      ) : (
        <p className="text-xs text-muted-foreground">
          {isRunning ? "No processing snapshot yet." : `Stopped · ${statusLabel}`}
        </p>
      )}
    </div>
  );
}
