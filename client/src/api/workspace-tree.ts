import { apiRequest } from "@/lib/api/client";
import type { SourceTreeSnapshot } from "@/types/chat";

type WorkspaceTreeNode = {
  id: string;
  kind: string;
  title: string;
  children: WorkspaceTreeNode[];
  document_id?: string | null;
  section_id?: string | null;
  page_number?: number | null;
  chunk_id?: string | null;
  asset_id?: string | null;
  status?: string | null;
  filename?: string | null;
  content_type?: string | null;
  page_start?: number | null;
  page_end?: number | null;
  asset_type?: string | null;
  thumbnail_url?: string | null;
  metadata?: Record<string, unknown>;
};

type WorkspaceTreeResponse = {
  domain_id: string;
  root: WorkspaceTreeNode;
};

export async function fetchWorkspaceTree(domainId: string): Promise<SourceTreeSnapshot> {
  const payload = await apiRequest<WorkspaceTreeResponse>(
    `/lightrag/domains/${encodeURIComponent(domainId)}/workspace-tree`,
  );
  return toSourceTree(payload.root);
}

function toSourceTree(root: WorkspaceTreeNode): SourceTreeSnapshot {
  const items: SourceTreeSnapshot["items"] = {};
  walkNode(root, items);
  return {
    root_id: root.id,
    items,
    expanded_item_ids: [root.id],
  };
}

function walkNode(node: WorkspaceTreeNode, items: SourceTreeSnapshot["items"]) {
  items[node.id] = {
    name: node.title,
    kind: node.kind,
    children: node.children.map((child) => child.id),
    handles: {
      node_id: node.id,
      node_kind: node.kind,
      document_id: node.document_id ?? null,
      section_id: node.section_id ?? null,
      page_number: node.page_number ?? null,
      chunk_id: node.chunk_id ?? null,
      asset_id: node.asset_id ?? null,
      status: node.status ?? null,
      filename: node.filename ?? null,
      content_type: node.content_type ?? null,
      page_start: node.page_start ?? null,
      page_end: node.page_end ?? null,
      asset_type: node.asset_type ?? null,
      thumbnail_url: node.thumbnail_url ?? null,
      metadata: node.metadata ?? {},
    },
  };
  for (const child of node.children) {
    walkNode(child, items);
  }
}
