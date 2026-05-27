import { apiRequest } from "@/lib/api/client";
import type { SourceTreeSnapshot } from "@/types/chat";

type WorkspaceTreeNode = {
  id: string;
  kind: string;
  title: string;
  children: WorkspaceTreeNode[];
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
    handles: { node_kind: node.kind },
  };
  for (const child of node.children) {
    walkNode(child, items);
  }
}
