import { StatusChip } from "@/components/surfaces/StatusChip";
import type { AdminDocument } from "@/lib/api/admin-documents";
import type { KnowledgeGraphDomain } from "@/lib/api/knowledge-graph-admin";

export function DomainOverviewCards({
  domains,
  documentsByDomainId,
}: {
  domains: KnowledgeGraphDomain[];
  documentsByDomainId: Map<string, AdminDocument[]>;
}) {
  const runningCount = domains.filter((domain) => {
    const statusLabel = domain.status || (domain.is_healthy ? "running" : "unknown");
    return statusLabel.toLowerCase() === "running" || domain.is_healthy === true;
  }).length;
  const indexingCount = domains.reduce((sum, domain) => {
    const docs = documentsByDomainId.get(domain.id) ?? [];
    return sum + docs.filter((doc) => doc.status === "indexing").length;
  }, 0);
  const failedCount = domains.reduce((sum, domain) => {
    const docs = documentsByDomainId.get(domain.id) ?? [];
    return sum + docs.filter((doc) => doc.status === "failed").length;
  }, 0);
  const docsCount = domains.reduce((sum, domain) => sum + (documentsByDomainId.get(domain.id)?.length ?? 0), 0);

  return (
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div className="space-y-1">
        <p className="text-sm font-semibold text-foreground">LightRAG Domains</p>
        <p className="text-xs text-muted-foreground">
          Runtime lifecycle board · {domains.length} domains · {docsCount} documents
        </p>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <StatusChip label={`${runningCount} running`} tone="success" />
        <StatusChip label={`${indexingCount} indexing`} tone="warning" />
        {failedCount > 0 ? <StatusChip label={`${failedCount} failed`} tone="danger" /> : null}
      </div>
    </div>
  );
}
