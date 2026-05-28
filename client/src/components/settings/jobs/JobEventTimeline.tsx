"use client";

import type { JobItem } from "@/api/jobs";

export function JobEventTimeline({ jobs }: { jobs: JobItem[] }) {
  const events = jobs.slice(0, 8).map((job) => ({
    id: `${job.id}-${job.updated_at}`,
    time: new Date(job.updated_at).toLocaleString(),
    type: job.kind,
    status: job.status,
    message: job.error_message || "Status updated",
    target: job.document_id ? `document ${job.document_id}` : "domain/workspace",
  }));

  return (
    <section className="rounded-xl border border-border bg-background p-4">
      <h3 className="text-sm font-medium text-foreground">Recent Events</h3>
      <div className="mt-3 space-y-2">
        {events.length === 0 ? <p className="text-xs text-muted-foreground">No recent events.</p> : null}
        {events.map((event) => (
          <article key={event.id} className="rounded-lg border border-border px-3 py-2 text-xs">
            <p className="text-foreground">{event.time} - {event.type} ({event.status})</p>
            <p className="text-muted-foreground">{event.target} - {event.message}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
