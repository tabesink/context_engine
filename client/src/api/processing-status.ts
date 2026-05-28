import { apiRequest } from "@/lib/api/client";

export type ProcessingCounts = {
  queued: number;
  indexing: number;
  ready: number;
  failed: number;
  deleted: number;
  unknown: number;
};

export type DomainProcessingStatus = {
  domain_id: string;
  state: "idle" | "queued" | "busy" | "partial_failure" | "failed" | "unreachable" | "unknown";
  is_busy: boolean;
  is_stale: boolean;
  updated_at: string;
  counts: ProcessingCounts;
  active?: {
    label?: string | null;
    current?: number | null;
    total?: number | null;
    message?: string | null;
    started_at?: string | null;
  } | null;
  documents?: Array<{
    document_id: string;
    filename: string;
    status: string;
    domain_id?: string | null;
    job_id?: string | null;
    job_status?: string | null;
    lightrag_status?: string | null;
    message?: string | null;
    can_retry: boolean;
    updated_at: string;
  }>;
  lightrag?: {
    reachable: boolean;
    pipeline_busy: boolean;
    job_name?: string | null;
    job_start?: string | null;
    latest_message?: string | null;
    history_tail: string[];
    update_status: Record<string, unknown>;
  } | null;
  errors: Array<{ code: string; message: string; source: string }>;
};

export type AdminDomainDocumentsProcessingStatus = {
  domain_id: string;
  documents: Array<{
    document_id: string;
    filename: string;
    status: string;
    domain_id?: string | null;
    job_id?: string | null;
    job_status?: string | null;
    lightrag_status?: string | null;
    message?: string | null;
    can_retry: boolean;
    updated_at: string;
  }>;
  status_counts: ProcessingCounts;
  pagination: {
    limit: number;
    offset: number;
    returned: number;
    total: number;
  };
  updated_at: string;
};

export function fetchUserDomainProcessingStatus(domainId: string) {
  return apiRequest<DomainProcessingStatus>(`/lightrag/domains/${encodeURIComponent(domainId)}/processing-status`);
}

export function fetchAdminDomainProcessingStatus(domainId: string) {
  return apiRequest<DomainProcessingStatus>(`/admin/lightrag/domains/${encodeURIComponent(domainId)}/processing-status`);
}

export function fetchAdminDomainDocumentsProcessingStatus(domainId: string, params?: { limit?: number; offset?: number }) {
  const query = new URLSearchParams();
  if (typeof params?.limit === "number") query.set("limit", String(params.limit));
  if (typeof params?.offset === "number") query.set("offset", String(params.offset));
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiRequest<AdminDomainDocumentsProcessingStatus>(
    `/admin/lightrag/domains/${encodeURIComponent(domainId)}/documents/processing-status${suffix}`,
  );
}
