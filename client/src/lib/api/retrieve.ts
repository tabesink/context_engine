import { apiRequest } from "@/lib/api/client";
import type { RetrievalSettings } from "@/types/chat";

export type RetrievalMode = "auto" | "semantic" | "navigation" | "hybrid";

export type RetrieveRequest = {
  query: string;
  mode: RetrievalMode;
  lightrag_domain_id: string;
  top_k?: number;
  include_assets?: boolean;
  include_thumbnails?: boolean;
};

export type RetrieveEvidence = {
  evidence_id: string;
  document_id: string;
  source_engine: string;
  text: string;
  score?: number | null;
  page_start?: number | null;
  page_end?: number | null;
  section_title?: string | null;
  source_path?: string | null;
  document_title?: string | null;
  chunk_id?: string | null;
  reference_id?: string | null;
  metadata: Record<string, unknown>;
};

export type RetrieveAsset = {
  asset_id: string;
  document_id: string;
  asset_type: string;
  caption?: string | null;
  page_number?: number | null;
  url: string;
  thumbnail_url?: string | null;
};

export type RetrieveResponse = {
  query: string;
  mode: RetrievalMode;
  evidence: RetrieveEvidence[];
  assets: RetrieveAsset[];
  debug?: Record<string, unknown> | null;
};

export const retrieveApi = {
  retrieve(request: RetrieveRequest) {
    return apiRequest<RetrieveResponse>("/retrieve", {
      method: "POST",
      body: JSON.stringify(request),
    });
  },
};

export function toRetrievalMode(mode: RetrievalSettings["mode"]): RetrievalMode {
  if (mode === "local") return "navigation";
  if (mode === "global" || mode === "naive") return "semantic";
  return "hybrid";
}
