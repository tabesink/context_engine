import { apiRequest } from "@/lib/api/client";
import type { WorkspaceSourceContext } from "@/types/chat";

export async function fetchWorkspaceSourceContext(
  domainId: string,
  nodeId: string,
): Promise<WorkspaceSourceContext> {
  const params = new URLSearchParams({ node_id: nodeId });
  return apiRequest<WorkspaceSourceContext>(
    `/lightrag/domains/${encodeURIComponent(domainId)}/workspace-context?${params.toString()}`,
  );
}
