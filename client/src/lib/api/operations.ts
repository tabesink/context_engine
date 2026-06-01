import { apiRequest } from "@/lib/api/client";

export type OperationStatus = "queued" | "running" | "succeeded" | "failed" | "canceled";

export type OperationStage =
  | "register_upload"
  | "parse_local_structure"
  | "push_to_lightrag"
  | "poll_remote_indexing"
  | "complete"
  | "failed";

export type Operation = {
  id: string;
  type: string;
  status: OperationStatus;
  stage?: OperationStage | string | null;
  progress?: number | null;
  resource_type?: "document" | "domain" | "provider" | "system" | string | null;
  resource_id?: string | null;
  resource_label?: string | null;
  actor_user_id?: string | null;
  message?: string | null;
  error_message?: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  updated_at: string;
};

export type ListOperationsParams = {
  limit?: number;
  offset?: number;
  resourceType?: string;
  resourceId?: string;
  status?: OperationStatus | string;
};

export const operationsApi = {
  list(params: ListOperationsParams = {}) {
    const search = new URLSearchParams();
    search.set("limit", String(params.limit ?? 50));
    search.set("offset", String(params.offset ?? 0));
    if (params.resourceType) search.set("resource_type", params.resourceType);
    if (params.resourceId) search.set("resource_id", params.resourceId);
    if (params.status) search.set("status", params.status);
    return apiRequest<Operation[]>(`/operations?${search.toString()}`);
  },
  get(operationId: string) {
    return apiRequest<Operation>(`/operations/${encodeURIComponent(operationId)}`);
  },
  retry(operationId: string) {
    return apiRequest<Operation>(`/operations/${encodeURIComponent(operationId)}/retry`, {
      method: "POST",
    });
  },
};

