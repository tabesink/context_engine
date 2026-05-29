import { apiRequest } from "@/lib/api/client";
import { getSelectedLightRagDomainId } from "@/stores/lightrag-domain-store";
import type {
  BackendStreamEvent,
  LightRagDomain,
  RetrievalSettings,
} from "@/types/chat";

type UserDomainPayload = {
  id: string;
  display_name: string;
  host_port: number;
  status?: string;
  is_healthy?: boolean;
  is_default?: boolean;
};

type StreamHandlers = {
  conversationId: string;
  query: string;
  retrievalSettings: RetrievalSettings;
  onMetadata?: (event: Extract<BackendStreamEvent, { event: "metadata" }>) => void;
  onProgress?: (event: Extract<BackendStreamEvent, { event: "progress" }>) => void;
  onContext?: (event: Extract<BackendStreamEvent, { event: "context" }>) => void;
  onChunk?: (chunk: string) => void;
};

export async function fetchLightRagDomains(): Promise<LightRagDomain[]> {
  const payload = await apiRequest<{ domains: UserDomainPayload[] }>("/lightrag/domains");
  return payload.domains.map((domain) => ({
    domain_id: domain.id,
    workspace: domain.display_name || domain.id,
    port: domain.host_port,
    service: domain.id,
    base_url: "",
    status: domain.status,
    is_healthy: domain.is_healthy,
    is_default: domain.is_default,
  }));
}

export async function streamBackendMessage(handlers: StreamHandlers): Promise<void> {
  const domainId = getSelectedLightRagDomainId();
  const response = await apiRequest<{
    query: string;
    evidence: Array<{ evidence_id: string; text: string }>;
  }>("/retrieve", {
    method: "POST",
    body: JSON.stringify({
      query: handlers.query,
      mode: mapMode(handlers.retrievalSettings.mode),
      top_k: handlers.retrievalSettings.top_k ?? 8,
      lightrag_domain_id: domainId,
    }),
  });
  handlers.onMetadata?.({
    event: "metadata",
    conversation_id: handlers.conversationId,
    user_message_id: `user-${Date.now()}`,
    assistant_message_id: `assistant-${Date.now()}`,
  });
  handlers.onChunk?.(response.evidence.map((item) => item.text).join("\n\n").trim() || "No response returned.");
}

function mapMode(mode: RetrievalSettings["mode"]) {
  if (mode === "local") return "navigation";
  if (mode === "global" || mode === "naive") return "semantic";
  return "hybrid";
}
