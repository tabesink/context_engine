import { apiRequest } from "@/lib/api/client";

export type JobItem = {
  id: string;
  kind: string;
  status: "queued" | "running" | "completed" | "failed" | "canceled" | "retrying" | string;
  document_id: string | null;
  error_message: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export function fetchJobs(params?: { limit?: number; offset?: number }) {
  const query = new URLSearchParams();
  if (typeof params?.limit === "number") query.set("limit", String(params.limit));
  if (typeof params?.offset === "number") query.set("offset", String(params.offset));
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiRequest<JobItem[]>(`/jobs${suffix}`);
}

export function retryJob(jobId: string) {
  return apiRequest<JobItem>(`/jobs/${encodeURIComponent(jobId)}/retry`, { method: "POST" });
}
