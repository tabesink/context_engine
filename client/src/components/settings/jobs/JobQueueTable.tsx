"use client";

import type { JobItem } from "@/api/jobs";
import { JobStatusChip } from "@/components/settings/jobs/JobStatusChip";
import { settingsCompactButtonClassName } from "@/components/settings/settings-controls";
import { Button } from "@/components/ui/button";

export function canRetryJob(job: JobItem) {
  return job.kind === "document_ingest" && (job.status === "failed" || job.status === "canceled");
}

type Props = {
  jobs: JobItem[];
  loading: boolean;
  onRetry: (jobId: string) => void;
  retryingJobId?: string | null;
};

export function JobQueueTable({ jobs, loading, onRetry, retryingJobId }: Props) {
  return (
    <section className="rounded-xl border border-border bg-background p-4">
      <h3 className="text-sm font-medium text-foreground">Jobs</h3>
      {loading ? <p className="mt-3 text-xs text-muted-foreground">Loading jobs...</p> : null}
      {!loading && jobs.length === 0 ? <p className="mt-3 text-xs text-muted-foreground">No jobs found.</p> : null}
      {jobs.length > 0 ? (
        <div className="mt-3 overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-xs">
            <thead className="text-muted-foreground">
              <tr>
                <th className="py-2">ID</th>
                <th className="py-2">Type</th>
                <th className="py-2">Status</th>
                <th className="py-2">Document</th>
                <th className="py-2">Updated</th>
                <th className="py-2">Message</th>
                <th className="py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => {
                const canRetry = canRetryJob(job);
                return (
                  <tr key={job.id} className="border-t border-border">
                    <td className="py-2 pr-2 font-mono text-[11px]">{job.id}</td>
                    <td className="py-2 pr-2">{job.kind}</td>
                    <td className="py-2 pr-2"><JobStatusChip status={job.status} /></td>
                    <td className="py-2 pr-2 font-mono text-[11px]">{job.document_id || "-"}</td>
                    <td className="py-2 pr-2">{new Date(job.updated_at).toLocaleString()}</td>
                    <td className="py-2 pr-2">{job.error_message || "-"}</td>
                    <td className="py-2">
                      {canRetry ? (
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          className={settingsCompactButtonClassName}
                          disabled={retryingJobId === job.id}
                          onClick={() => onRetry(job.id)}
                        >
                          {retryingJobId === job.id ? "Retrying..." : "Retry"}
                        </Button>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}
