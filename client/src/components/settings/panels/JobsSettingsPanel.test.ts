import { describe, expect, it, vi } from "vitest";

import type { JobItem } from "@/api/jobs";
import { canRetryJob } from "@/components/settings/jobs/JobQueueTable";
import { countsFromJobs, filterJobsByStatus } from "@/components/settings/panels/JobsSettingsPanel";

function makeJob(overrides: Partial<JobItem>): JobItem {
  return {
    id: "job-1",
    kind: "document_ingest",
    status: "queued",
    document_id: "doc-1",
    error_message: null,
    metadata: {},
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("jobs panel logic", () => {
  it("counts statuses for overview", () => {
    const jobs = [
      makeJob({ id: "q", status: "queued" }),
      makeJob({ id: "r", status: "running" }),
      makeJob({ id: "f", status: "failed" }),
      makeJob({ id: "c", status: "completed" }),
    ];

    expect(countsFromJobs(jobs)).toEqual({ queued: 1, running: 1, completed: 1, failed: 1 });
  });

  it("filters jobs by status", () => {
    const jobs = [
      makeJob({ id: "q", status: "queued" }),
      makeJob({ id: "r", status: "running" }),
      makeJob({ id: "f", status: "failed" }),
    ];

    expect(filterJobsByStatus(jobs, "all")).toHaveLength(3);
    expect(filterJobsByStatus(jobs, "failed").map((job) => job.id)).toEqual(["f"]);
  });

  it("allows retry only for document_ingest failed or canceled jobs", () => {
    expect(canRetryJob(makeJob({ kind: "document_ingest", status: "failed" }))).toBe(true);
    expect(canRetryJob(makeJob({ kind: "document_ingest", status: "canceled" }))).toBe(true);
    expect(canRetryJob(makeJob({ kind: "document_ingest", status: "running" }))).toBe(false);
    expect(canRetryJob(makeJob({ kind: "other", status: "failed" }))).toBe(false);
  });

  it("schedules and clears polling timers", async () => {
    vi.useFakeTimers();
    const tick = vi.fn(async () => [] as JobItem[]);

    const { createAdaptivePollingController } = await import("@/hooks/use-adaptive-polling");
    const controller = createAdaptivePollingController({
      run: tick,
      getDelay: () => 10000,
      errorDelayMs: 10000,
      initialDelayMs: 0,
    });

    controller.start();
    await vi.runOnlyPendingTimersAsync();
    expect(tick).toHaveBeenCalledTimes(1);
    controller.stop();
    await vi.advanceTimersByTimeAsync(20000);
    expect(tick).toHaveBeenCalledTimes(1);
    vi.useRealTimers();
  });
});
