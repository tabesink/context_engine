import { StatusChip } from "@/components/surfaces/StatusChip";
import { toneForProcessingStatus } from "@/components/surfaces/status-tone";
import type { AdminDomainDocumentsProcessingStatus } from "@/api/processing-status";

type RowStatus = AdminDomainDocumentsProcessingStatus["documents"][number]["status"];

function labelForStatus(status: RowStatus) {
  if (status === "ready") return "Complete";
  if (status === "indexing") return "Indexing";
  if (status === "uploaded") return "Uploaded";
  if (status === "queued") return "Queued";
  if (status === "failed") return "Failed";
  return status;
}

export function DocumentStatusChip({ status, showDot = false }: { status: RowStatus; showDot?: boolean }) {
  return <StatusChip label={labelForStatus(status)} tone={toneForProcessingStatus(status)} dot={showDot} />;
}
