import { apiRequest } from "@/lib/api/client";
import type { LightRagDomain } from "@/types/chat";

export type CreateKnowledgeGraphDomainPayload = {
  domain_id: string;
  display_name?: string;
  host_port?: number;
  embedding_profile_id?: string;
};

export type KnowledgeGraphDomain = LightRagDomain & {
  id: string;
  display_name: string;
  host_port?: number;
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
};

type FirstClassAdminDomain = {
  id: string;
  display_name: string;
  state?: string;
  health_status?: string | null;
  metadata?: Record<string, unknown> | null;
};

export const knowledgeGraphAdminApi = {
  async list() {
    const payload = await apiRequest<{ domains: FirstClassAdminDomain[] }>("/admin/lightrag-domains");
    return payload.domains.map(toKnowledgeGraphDomainFromFirstClass);
  },
  async create(request: CreateKnowledgeGraphDomainPayload) {
    const domain = await apiRequest<AdminDomain>("/admin/lightrag-domains", {
      method: "POST",
      body: JSON.stringify(request),
    });
    return toKnowledgeGraphDomain(domain);
  },
  up(domainId: string) {
    return apiRequest(`/admin/lightrag-domains/${encodeURIComponent(domainId)}/start`, {
      method: "POST",
    });
  },
  down(domainId: string) {
    return apiRequest(`/admin/lightrag-domains/${encodeURIComponent(domainId)}/stop`, {
      method: "POST",
    });
  },
  remove(domainId: string) {
    return apiRequest(`/admin/lightrag-domains/${encodeURIComponent(domainId)}`, { method: "DELETE" });
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

function toKnowledgeGraphDomainFromFirstClass(domain: FirstClassAdminDomain): KnowledgeGraphDomain {
  const metadata = domain.metadata ?? {};
  const hostPort =
    typeof metadata.host_port === "number"
      ? metadata.host_port
      : typeof metadata.host_port === "string"
        ? Number.parseInt(metadata.host_port, 10)
        : undefined;
  const status = domain.state === "failed" ? "error" : domain.state;
  const isHealthy = domain.health_status === "healthy" ? true : domain.health_status === "unhealthy" ? false : undefined;
  return {
    id: domain.id,
    display_name: domain.display_name || domain.id,
    domain_id: domain.id,
    workspace: domain.display_name || domain.id,
    port: hostPort ?? 0,
    service: domain.id,
    base_url: "",
    status,
    is_healthy: isHealthy,
    is_default: false,
    host_port: hostPort,
    embedding: null,
  };
}
