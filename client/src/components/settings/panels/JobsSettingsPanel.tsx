"use client";

import * as React from "react";
import { fetchJobs, retryJob, type JobItem } from "@/api/jobs";
import { JobEventTimeline } from "@/components/settings/jobs/JobEventTimeline";
import { JobQueueOverview } from "@/components/settings/jobs/JobQueueOverview";
import { JobQueueTable } from "@/components/settings/jobs/JobQueueTable";
import { PanelState } from "@/components/surfaces/PanelState";
import { useAdaptivePolling } from "@/hooks/use-adaptive-polling";
import { settingsCompactSelectClassName, settingsPanelContentClassName } from "@/components/settings/settings-controls";
import { selectIsAdmin, useAuthStore } from "@/stores/auth-store";

export function countsFromJobs(jobs: JobItem[]) {
  return jobs.reduce(
    (acc, job) => {
      const value = job.status.toLowerCase();
      if (value === "queued") acc.queued += 1;
      else if (value === "running") acc.running += 1;
      else if (value === "completed") acc.completed += 1;
      else if (value === "failed") acc.failed += 1;
      return acc;
    },
    { queued: 0, running: 0, completed: 0, failed: 0 },
  );
}

export function filterJobsByStatus(jobs: JobItem[], filter: string) {
  if (filter === "all") return jobs;
  return jobs.filter((job) => job.status.toLowerCase() === filter.toLowerCase());
}

export function JobsSettingsPanel() {
  const isAdmin = useAuthStore(selectIsAdmin);
  const [jobs, setJobs] = React.useState<JobItem[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [retryingJobId, setRetryingJobId] = React.useState<string | null>(null);
  const [statusFilter, setStatusFilter] = React.useState<string>("all");

  const load = React.useCallback(async () => {
    setLoading((current) => current || jobs.length === 0);
    try {
      const response = await fetchJobs({ limit: 100, offset: 0 });
      setJobs(response);
      setError(null);
      return response;
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Failed to load jobs.");
      return jobs;
    } finally {
      setLoading(false);
    }
  }, [jobs]);

  useAdaptivePolling({
    enabled: isAdmin,
    run: load,
    getDelay: () => 10000,
    errorDelayMs: 10000,
    initialDelayMs: 0,
  });

  const onRetry = async (jobId: string) => {
    setRetryingJobId(jobId);
    try {
      await retryJob(jobId);
      await load();
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : "Retry failed.");
    } finally {
      setRetryingJobId(null);
    }
  };

  if (!isAdmin) {
    return <PanelState title="Admin access required" description="Sign in as an admin to view jobs and events." />;
  }

  const filteredJobs = filterJobsByStatus(jobs, statusFilter);

  return (
    <div className={settingsPanelContentClassName}>
      <JobQueueOverview counts={countsFromJobs(jobs)} />
      <section className="rounded-xl border border-border bg-background p-4">
        <div className="flex items-center gap-3">
          <label htmlFor="jobs-status-filter" className="text-xs text-muted-foreground">Status filter</label>
          <select
            id="jobs-status-filter"
            className={settingsCompactSelectClassName}
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
          >
            <option value="all">All</option>
            <option value="queued">Queued</option>
            <option value="running">Running</option>
            <option value="failed">Failed</option>
            <option value="completed">Completed</option>
            <option value="canceled">Canceled</option>
          </select>
        </div>
      </section>
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
      <JobQueueTable jobs={filteredJobs} loading={loading} onRetry={(jobId) => void onRetry(jobId)} retryingJobId={retryingJobId} />
      <JobEventTimeline jobs={filteredJobs} />
    </div>
  );
}
