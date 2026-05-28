import { apiRequest } from "@/lib/api/client";
import type { LightRagDomain } from "@/types/chat";
import type { RetrievalDefaults } from "@/types/lightrag";

export type CreateKnowledgeGraphDomainPayload = {
  domain_id: string;
  display_name?: string;
  host_port?: number;
  embedding_profile_id?: string;
  start?: boolean;
  top_k?: number;
  chunk_top_k?: number;
  chunk_rerank_top_k?: number;
  max_token_for_text_unit?: number;
  max_token_for_global_context?: number;
  max_token_for_local_context?: number;
};

export type KnowledgeGraphDomain = LightRagDomain & {
  id: string;
  display_name: string;
  host_port: number;
  embedding?: {
    profile_id: string;
    model: string;
    dimensions?: number | null;
  } | null;
};

type AdminDomain = {
  id: string;
  display_name: string;
  host_port: number;
  status?: string;
  is_healthy?: boolean;
  is_default?: boolean;
  embedding?: {
    profile_id: string;
    model: string;
    dimensions?: number | null;
  } | null;
  retrieval_defaults?: RetrievalDefaults;
};

export const knowledgeGraphAdminApi = {
  async list() {
    const payload = await apiRequest<{ domains: AdminDomain[] }>("/admin/lightrag/domains");
    return payload.domains.map(toKnowledgeGraphDomain);
  },
  async create(request: CreateKnowledgeGraphDomainPayload) {
    const domain = await apiRequest<AdminDomain>("/admin/lightrag/domains", {
      method: "POST",
      body: JSON.stringify(request),
    });
    return toKnowledgeGraphDomain(domain);
  },
  up(domainId: string) {
    return apiRequest(`/admin/lightrag/domains/${encodeURIComponent(domainId)}/up`, { method: "POST" });
  },
  down(domainId: string) {
    return apiRequest(`/admin/lightrag/domains/${encodeURIComponent(domainId)}/down`, { method: "POST" });
  },
  recreate(domainId: string) {
    return apiRequest(`/admin/lightrag/domains/${encodeURIComponent(domainId)}/recreate`, {
      method: "POST",
    });
  },
  repair(domainId: string) {
    return apiRequest(`/admin/lightrag/domains/${encodeURIComponent(domainId)}/repair`, {
      method: "POST",
    });
  },
  regenerate(domainId: string) {
    return apiRequest(`/admin/lightrag/domains/${encodeURIComponent(domainId)}/regenerate`, {
      method: "POST",
    });
  },
  remove(domainId: string) {
    return apiRequest(`/admin/lightrag/domains/${encodeURIComponent(domainId)}`, {
      method: "DELETE",
    });
  },
  purgePreview(domainId: string) {
    return apiRequest<{
      domain_id: string;
      document_count: number;
      active_jobs: number;
    }>(`/admin/lightrag/domains/${encodeURIComponent(domainId)}/purge-preview`, {
      method: "POST",
    });
  },
  purge(domainId: string) {
    return apiRequest(`/admin/lightrag/domains/${encodeURIComponent(domainId)}/purge?confirm_domain_id=${encodeURIComponent(domainId)}`, {
      method: "DELETE",
    });
  },
};

function toKnowledgeGraphDomain(domain: AdminDomain): KnowledgeGraphDomain {
  return {
    id: domain.id,
    display_name: domain.display_name || domain.id,
    domain_id: domain.id,
    workspace: domain.display_name || domain.id,
    port: domain.host_port,
    service: domain.id,
    base_url: "",
    status: domain.status,
    is_healthy: domain.is_healthy,
    is_default: domain.is_default,
    retrieval_defaults: domain.retrieval_defaults,
    host_port: domain.host_port,
    embedding: domain.embedding
      ? {
          profile_id: domain.embedding.profile_id,
          model: domain.embedding.model,
          dimensions: domain.embedding.dimensions ?? null,
        }
      : null,
  };
}
