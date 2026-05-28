"use client";

import { FileIcon, FolderIcon, FolderOpenIcon } from "lucide-react";
import { hotkeysCoreFeature, syncDataLoaderFeature } from "@headless-tree/core";
import { useTree } from "@headless-tree/react";
import { Tree, TreeItem, TreeItemLabel } from "@/components/reui/tree";
import type { SourceTreeItem, SourceTreeSnapshot } from "@/types/chat";

const emptyTree: SourceTreeSnapshot = {
  root_id: "root",
  items: {
    root: { name: "Root", children: ["workspace"] },
    workspace: { name: "Workspace", children: [] },
  },
  expanded_item_ids: ["root", "workspace"],
};

const indent = 20;

type WorkspaceTreeProps = {
  sourceTree?: SourceTreeSnapshot | null;
  selectedNodeId?: string;
  onNodeSelect?: (nodeId: string, item: SourceTreeItem) => void;
  loading?: boolean;
  error?: string;
};

export function WorkspaceTree({ sourceTree, selectedNodeId, onNodeSelect, loading, error }: WorkspaceTreeProps) {
  const data = normalizeSourceTree(sourceTree);
  const revision = sourceTreeRevision(data);

  return (
    <WorkspaceTreeContent
      key={revision}
      sourceTree={data}
      selectedNodeId={selectedNodeId}
      onNodeSelect={onNodeSelect}
      loading={loading}
      error={error}
    />
  );
}

function WorkspaceTreeContent({
  sourceTree,
  selectedNodeId,
  onNodeSelect,
  loading,
  error,
}: {
  sourceTree: SourceTreeSnapshot;
  selectedNodeId?: string;
  onNodeSelect?: (nodeId: string, item: SourceTreeItem) => void;
  loading?: boolean;
  error?: string;
}) {
  const data = sourceTree;
  const tree = useTree<SourceTreeItem>({
    initialState: {
      expandedItems: data.expanded_item_ids ?? ["root", "workspace"],
    },
    indent,
    rootItemId: data.root_id,
    getItemName: (item) => item.getItemData().name,
    isItemFolder: (item) => (item.getItemData().children?.length ?? 0) > 0,
    dataLoader: {
      getItem: (itemId) => data.items[itemId] ?? { name: itemId },
      getChildren: (itemId) => data.items[itemId]?.children ?? [],
    },
    features: [syncDataLoaderFeature, hotkeysCoreFeature],
  });

  const rootChildren = data.items[data.root_id]?.children ?? [];
  const hasDocuments = rootChildren.length > 0;

  return (
    <div className="w-full bg-transparent">
      <div className="mb-3">
        <p className="text-xs font-medium uppercase tracking-wide text-[var(--muted-foreground)]">Sources</p>
        <p className="mt-1 text-xs leading-5 text-[var(--muted-foreground)]">Indexed document map</p>
      </div>
      {loading ? (
        <p className="mb-3 text-xs leading-5 text-[var(--muted-foreground)]">Loading sources…</p>
      ) : null}
      {error ? (
        <p className="mb-3 rounded-lg border border-border bg-muted/30 px-2.5 py-2 text-xs leading-5 text-[var(--muted-foreground)]">
          {error}
        </p>
      ) : null}
      <Tree
        className="relative w-full"
        indent={indent}
        label="Workspace source tree"
        tree={tree}
      >
        {tree.getItems().map((item) => {
          const itemId = item.getId();
          const selected = itemId === selectedNodeId;
          return (
            <TreeItem
              key={itemId}
              className="bg-[repeating-linear-gradient(to_right,transparent_0,transparent_calc(var(--tree-indent)-1px),var(--border)_calc(var(--tree-indent)-1px),var(--border)_var(--tree-indent))] bg-[length:var(--tree-item-indent)_100%] bg-no-repeat"
              item={item}
            >
              <TreeItemLabel
                onClick={() => onNodeSelect?.(itemId, item.getItemData())}
                className={[
                  "relative py-1 before:absolute before:inset-x-0 before:-inset-y-0.5 before:-z-10 before:bg-[var(--background)] text-xs leading-5 text-[var(--foreground)] hover:bg-[var(--muted)]",
                  selected ? "bg-[var(--muted)]" : "",
                ].join(" ")}
              >
                <span className="flex min-w-0 items-center gap-1.5">
                  {item.isFolder() ? (
                    item.isExpanded() ? (
                      <FolderOpenIcon className="pointer-events-none size-3.5 shrink-0 text-[var(--muted-foreground)]" aria-hidden />
                    ) : (
                      <FolderIcon className="pointer-events-none size-3.5 shrink-0 text-[var(--muted-foreground)]" aria-hidden />
                    )
                  ) : (
                    <FileIcon className="pointer-events-none size-3.5 shrink-0 text-[var(--muted-foreground)]" aria-hidden />
                  )}
                  <span className="truncate">{item.getItemName()}</span>
                </span>
              </TreeItemLabel>
            </TreeItem>
          );
        })}
      </Tree>
      {!loading && !error && !hasDocuments ? (
        <p className="mt-3 text-xs leading-5 text-[var(--muted-foreground)]">
          Indexed documents will appear here once processing completes.
        </p>
      ) : null}
    </div>
  );
}

function normalizeSourceTree(sourceTree?: SourceTreeSnapshot | null): SourceTreeSnapshot {
  if (!sourceTree?.items?.[sourceTree.root_id]) {
    return emptyTree;
  }
  return sourceTree;
}

function sourceTreeRevision(sourceTree: SourceTreeSnapshot) {
  return Object.entries(sourceTree.items)
    .map(([itemId, item]) => `${itemId}:${item.children?.length ?? 0}:${item.retrieval_frame_ids?.length ?? 0}`)
    .sort()
    .join("|");
}
