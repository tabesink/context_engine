import { Progress } from "@/components/ui/progress";
import { settingsCompactSelectClassName } from "@/components/settings/settings-controls";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { ProcessingCounts } from "@/api/processing-status";

function LegendDot({ className }: { className: string }) {
  return <span className={`size-1.5 rounded-full ${className}`} aria-hidden />;
}

export function DocumentProcessingOverview({
  domains,
  domainId,
  counts,
  onDomainChange,
}: {
  domains: Array<{ id: string; display_name: string }>;
  domainId: string;
  counts?: ProcessingCounts;
  onDomainChange: (value: string) => void;
}) {
  const total = counts
    ? counts.queued + counts.indexing + counts.ready + counts.failed + counts.deleted + counts.unknown
    : 0;
  const completed = counts ? counts.ready + counts.failed + counts.deleted : 0;
  const progress = total > 0 ? Math.round((completed / total) * 100) : 0;
  const processing = counts ? counts.queued + counts.indexing : 0;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-1">
          <p className="text-sm font-semibold text-foreground">PDF Processing</p>
          <p className="text-xs text-muted-foreground">Document extraction queue</p>
        </div>
        <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
          {counts ? (
            <>
              <span className="inline-flex items-center gap-1.5">
                <LegendDot className="bg-emerald-500" />
                {counts.ready} complete
              </span>
              <span className="inline-flex items-center gap-1.5">
                <LegendDot className="bg-amber-500" />
                {processing} processing
              </span>
              {counts.failed > 0 ? (
                <span className="inline-flex items-center gap-1.5">
                  <LegendDot className="bg-destructive" />
                  {counts.failed} failed
                </span>
              ) : null}
            </>
          ) : null}
        </div>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Select value={domainId} onValueChange={onDomainChange}>
          <SelectTrigger className={`${settingsCompactSelectClassName} w-[280px]`}>
            <SelectValue placeholder="Select domain" />
          </SelectTrigger>
          <SelectContent>
            {domains.map((item) => (
              <SelectItem key={item.id} value={item.id}>
                {item.display_name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <div className="min-w-[180px] space-y-1">
          <Progress value={progress} className="h-1" />
          <p className="text-right text-[11px] text-muted-foreground">{progress}% complete</p>
        </div>
      </div>
    </div>
  );
}
