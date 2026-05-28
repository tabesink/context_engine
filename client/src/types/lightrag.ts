export type RetrievalDefaults = {
  top_k: number;
  chunk_top_k: number;
  chunk_rerank_top_k: number;
  max_token_for_text_unit: number;
  max_token_for_global_context: number;
  max_token_for_local_context: number;
};

export type LightRagDomainSummary = {
  id: string;
  display_name: string;
  host_port: number | null;
  is_healthy: boolean | null;
  is_default: boolean;
  status: string | null;
  retrieval_defaults?: RetrievalDefaults;
};

export type VisualAsset = {
  asset_id: string;
  document_id: string | null;
  asset_type: string | null;
  title: string;
  caption?: string | null;
  page_number?: number | null;
  section_id?: string | null;
  url?: string | null;
  thumbnail_url?: string | null;
  mime_type?: string | null;
  metadata?: Record<string, unknown> | null;
};
