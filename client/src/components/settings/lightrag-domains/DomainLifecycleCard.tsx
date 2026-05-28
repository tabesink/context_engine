import { Database, MoreHorizontal } from "lucide-react";
import type { DomainProcessingStatus } from "@/api/processing-status";
import { settingsCompactButtonClassName } from "@/components/settings/settings-controls";
import { DomainEventsTable } from "@/components/settings/lightrag-domains/DomainEventsTable";
import { DomainRuntimeStatusInline } from "@/components/settings/lightrag-domains/DomainRuntimeStatusInline";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { AdminAuditLog, AdminDocument } from "@/lib/api/admin-documents";
import type { KnowledgeGraphDomain } from "@/lib/api/knowledge-graph-admin";

type DomainAction = "up" | "down" | "repair" | "archive" | "purge";
type AdvancedAction = "recreate" | "regenerate";

function statusDotClassName(isRunning: boolean) {
  return isRunning ? "bg-emerald-500" : "bg-muted-foreground";
}

export function DomainLifecycleCard({
  domain,
  documents,
  logs,
  processingStatus,
  busyAction,
  uploadBusy,
  onRunAction,
  onRunAdvancedAction,
  onUpload,
  onOpenDocuments,
  onOpenLogs,
  onArchive,
  onPreviewPurge,
  onPurge,
}: {
  domain: KnowledgeGraphDomain;
  documents: AdminDocument[];
  logs: AdminAuditLog[];
  processingStatus: DomainProcessingStatus | null | undefined;
  busyAction: DomainAction | null | undefined;
  uploadBusy: boolean;
  onRunAction: (domainId: string, action: DomainAction) => void;
  onRunAdvancedAction: (domainId: string, action: AdvancedAction) => void;
  onUpload: (domainId: string) => void;
  onOpenDocuments: (domainId: string) => void;
  onOpenLogs: (domainId: string) => void;
  onArchive: (domainId: string) => void;
  onPreviewPurge: (domainId: string) => void;
  onPurge: (domainId: string) => void;
}) {
  const statusLabel = domain.status || (domain.is_healthy ? "running" : "unknown");
  const isRunning = statusLabel.toLowerCase() === "running" || domain.is_healthy === true;
  const docsCount = documents.length;
  const embeddingLabel = domain.embedding
    ? `${domain.embedding.model}${domain.embedding.dimensions ? ` · ${domain.embedding.dimensions} dims` : ""}`
    : "Legacy / unknown embedding";

  return (
    <Card className="gap-0 py-0 shadow-sm">
      <CardHeader className="border-b border-border px-5 py-4">
        <div className="flex items-start gap-3">
          <span className={`mt-2 size-2 shrink-0 rounded-full ${statusDotClassName(isRunning)}`} aria-hidden />
          <div className="min-w-0 flex-1">
            <div className="flex min-w-0 items-center gap-2">
              <Database className="size-4 shrink-0 text-muted-foreground/70" aria-hidden />
              <p className="truncate text-sm font-semibold text-foreground">{domain.display_name || domain.id}</p>
            </div>
            <p className="mt-1 truncate pl-6 text-xs text-muted-foreground">
              Port {domain.host_port} · {docsCount} documents · {embeddingLabel}
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="grid gap-6 px-5 py-4 md:grid-cols-2">
        <div className="space-y-4">
          <DomainRuntimeStatusInline domain={domain} status={processingStatus} />
          <div className="space-y-2">
            <p className="text-sm font-medium text-foreground">Quick actions</p>
            <div className="flex flex-wrap gap-1.5">
              {isRunning ? (
                <Button
                  size="sm"
                  variant="outline"
                  disabled={Boolean(busyAction)}
                  onClick={() => onRunAction(domain.id, "down")}
                  className={settingsCompactButtonClassName}
                >
                  {busyAction === "down" ? "Stopping..." : "Stop runtime"}
                </Button>
              ) : (
                <Button
                  size="sm"
                  variant="outline"
                  disabled={Boolean(busyAction)}
                  onClick={() => onRunAction(domain.id, "up")}
                  className={settingsCompactButtonClassName}
                >
                  {busyAction === "up" ? "Starting..." : "Start runtime"}
                </Button>
              )}
              <Button
                size="sm"
                variant="outline"
                disabled={!isRunning || uploadBusy}
                onClick={() => onUpload(domain.id)}
                className={settingsCompactButtonClassName}
              >
                {uploadBusy ? "Uploading..." : "Upload document"}
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => onOpenDocuments(domain.id)}
                className={settingsCompactButtonClassName}
              >
                View documents
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => onOpenLogs(domain.id)}
                className={settingsCompactButtonClassName}
              >
                Event tail
              </Button>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    size="sm"
                    variant="outline"
                    className={`${settingsCompactButtonClassName} px-2.5`}
                    aria-label="More domain actions"
                  >
                    <MoreHorizontal className="size-4" />
                    More
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start" className="shadow-none">
                  <DropdownMenuLabel>Lifecycle</DropdownMenuLabel>
                  <DropdownMenuItem disabled={Boolean(busyAction)} onClick={() => onRunAction(domain.id, "repair")}>
                    Repair
                  </DropdownMenuItem>
                  <DropdownMenuItem disabled={Boolean(busyAction)} onClick={() => onRunAdvancedAction(domain.id, "recreate")}>
                    Recreate container
                  </DropdownMenuItem>
                  <DropdownMenuItem disabled={Boolean(busyAction)} onClick={() => onRunAdvancedAction(domain.id, "regenerate")}>
                    Regenerate config
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuLabel>Danger zone</DropdownMenuLabel>
                  <DropdownMenuItem disabled={Boolean(busyAction)} onClick={() => onArchive(domain.id)}>
                    Archive
                  </DropdownMenuItem>
                  <DropdownMenuItem disabled={Boolean(busyAction)} onClick={() => onPreviewPurge(domain.id)}>
                    Preview purge
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    disabled={Boolean(busyAction)}
                    onClick={() => onPurge(domain.id)}
                    className="text-destructive focus:text-destructive"
                  >
                    Purge permanently
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>
        <DomainEventsTable domainId={domain.id} logs={logs} />
      </CardContent>
    </Card>
  );
}
