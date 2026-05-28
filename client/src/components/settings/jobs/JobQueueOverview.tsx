"use client";

import { StatusChip } from "@/components/surfaces/StatusChip";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type JobCounts = {
  queued: number;
  running: number;
  completed: number;
  failed: number;
};

export function JobQueueOverview({ counts }: { counts: JobCounts }) {
  return (
    <Card className="rounded-xl border border-border bg-background shadow-none">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium">Queue Overview</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-2 sm:grid-cols-4">
        <StatusChip label={`Queued ${counts.queued}`} tone="warning" dot={false} />
        <StatusChip label={`Running ${counts.running}`} tone="info" dot={false} />
        <StatusChip label={`Completed ${counts.completed}`} tone="success" dot={false} />
        <StatusChip label={`Failed ${counts.failed}`} tone="danger" dot={false} />
      </CardContent>
    </Card>
  );
}
