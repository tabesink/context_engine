import { APIError, apiRequest, getAccessToken, resolveApiBase } from "@/lib/api/client";

export type AdminDocument = {
  id: string;
  filename: string;
  content_type: string;
  status: "uploaded" | "indexing" | "ready" | "failed" | "deleted";
  created_at: string;
  updated_at: string;
  metadata: Record<string, unknown>;
  error_message?: string | null;
};

export type AdminDocumentUploadResponse = {
  document: AdminDocument;
  job_id?: string | null;
};

export type AdminAuditLog = {
  id: number;
  event: string;
  target_id: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

export const adminDocumentsApi = {
  list(limit = 500) {
    return apiRequest<AdminDocument[]>(`/admin/documents?limit=${limit}&offset=0`);
  },
  listAuditLogs(limit = 500) {
    return apiRequest<AdminAuditLog[]>(`/admin/audit-logs?limit=${limit}&offset=0`);
  },
  async uploadToDomain(file: File, lightragDomainId: string): Promise<AdminDocumentUploadResponse> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("lightrag_domain_id", lightragDomainId);

    const headers = new Headers();
    const token = getAccessToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    headers.set("Accept", "application/json");

    const response = await fetch(`${resolveApiBase()}/admin/documents/upload`, {
      method: "POST",
      headers,
      body: formData,
      credentials: "omit",
    });

    const payload = await readBody(response);
    if (!response.ok) {
      throw new APIError(extractDetail(payload) || `${response.status} ${response.statusText}`, response.status, payload);
    }
    return payload as AdminDocumentUploadResponse;
  },
  reingest(documentId: string) {
    return apiRequest<{ document_id: string; job_id: string }>(
      `/admin/documents/${encodeURIComponent(documentId)}/reingest`,
      { method: "POST" },
    );
  },
};

async function readBody(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    try {
      return await response.json();
    } catch {
      return null;
    }
  }
  const text = await response.text();
  return text || null;
}

function extractDetail(body: unknown): string {
  if (typeof body === "string") return body;
  if (body && typeof body === "object" && "detail" in body && typeof body.detail === "string") {
    return body.detail;
  }
  return "";
}
