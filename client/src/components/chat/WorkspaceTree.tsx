"use client";

import { useMemo, useState } from "react";
import { ChevronRight, FileIcon, FolderIcon, FolderOpenIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import type { SourceTreeItem, SourceTreeSnapshot } from "@/types/chat";

const emptyTree: SourceTreeSnapshot = {
  root_id: "root",
  items: {
    root: { name: "Root", children: ["workspace"] },
    workspace: { name: "Workspace", children: [] },
  },
  expanded_item_ids: ["root", "workspace"],
};

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
      data={data}
      selectedNodeId={selectedNodeId}
      onNodeSelect={onNodeSelect}
      loading={loading}
      error={error}
    />
  );
}

function WorkspaceTreeContent({
  data,
  selectedNodeId,
  onNodeSelect,
  loading,
  error,
}: {
  data: SourceTreeSnapshot;
  selectedNodeId?: string;
  onNodeSelect?: (nodeId: string, item: SourceTreeItem) => void;
  loading?: boolean;
  error?: string;
}) {
  const [expandedIds, setExpandedIds] = useState(
    () => new Set(data.expanded_item_ids ?? [data.root_id]),
  );

  const hasDocuments = useMemo(() => hasTreeDocuments(data), [data]);
  const rootItem = data.items[data.root_id];

  const toggleExpanded = (nodeId: string) => {
    setExpandedIds((current) => {
      const next = new Set(current);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  };

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
      {rootItem ? (
        <div role="tree" aria-label="Workspace source tree" className="relative w-full">
          <SourceTreeNodes
            sourceTree={data}
            nodeIds={[data.root_id]}
            depth={0}
            expandedIds={expandedIds}
            selectedNodeId={selectedNodeId}
            onToggleExpanded={toggleExpanded}
            onNodeSelect={onNodeSelect}
          />
        </div>
      ) : null}
      {!loading && !error && !hasDocuments ? (
        <p className="mt-3 text-xs leading-5 text-[var(--muted-foreground)]">
          No documents in this knowledge graph yet. Upload files to this domain in Settings to populate the tree.
        </p>
      ) : null}
    </div>
  );
}

function SourceTreeNodes({
  sourceTree,
  nodeIds,
  depth,
  expandedIds,
  selectedNodeId,
  onToggleExpanded,
  onNodeSelect,
}: {
  sourceTree: SourceTreeSnapshot;
  nodeIds: string[];
  depth: number;
  expandedIds: Set<string>;
  selectedNodeId?: string;
  onToggleExpanded: (nodeId: string) => void;
  onNodeSelect?: (nodeId: string, item: SourceTreeItem) => void;
}) {
  return nodeIds.map((nodeId) => {
    const item = sourceTree.items[nodeId];
    if (!item) return null;

    const childIds = item.children ?? [];
    const isFolder = childIds.length > 0;
    const isExpanded = expandedIds.has(nodeId);
    const selected = nodeId === selectedNodeId;
    const statusLabel = formatTreeStatus(item.handles?.status);
    const indentPx = depth * 20;

    return (
      <div
        key={nodeId}
        role="treeitem"
        aria-selected={selected}
        aria-expanded={isFolder ? isExpanded : undefined}
      >
        <div
          className={cn(
            "flex min-w-0 items-center gap-0.5 rounded-md py-1 text-xs leading-5 text-[var(--foreground)] hover:bg-[var(--muted)]",
            selected ? "bg-[var(--muted)]" : "",
          )}
          style={{ paddingInlineStart: `${indentPx}px` }}
        >
          {isFolder ? (
            <button
              type="button"
              aria-label={isExpanded ? "Collapse folder" : "Expand folder"}
              onClick={() => onToggleExpanded(nodeId)}
              className="inline-flex size-5 shrink-0 items-center justify-center rounded text-[var(--muted-foreground)] hover:bg-[var(--secondary)]"
            >
              <ChevronRight className={cn("size-3.5 transition-transform", isExpanded ? "rotate-90" : "")} aria-hidden />
            </button>
          ) : (
            <span className="inline-block size-5 shrink-0" aria-hidden />
          )}
          <button
            type="button"
            onClick={() => onNodeSelect?.(nodeId, item)}
            className="flex min-w-0 flex-1 items-center gap-1.5 text-left"
          >
            {isFolder ? (
              isExpanded ? (
                <FolderOpenIcon className="pointer-events-none size-3.5 shrink-0 text-[var(--muted-foreground)]" aria-hidden />
              ) : (
                <FolderIcon className="pointer-events-none size-3.5 shrink-0 text-[var(--muted-foreground)]" aria-hidden />
              )
            ) : (
              <FileIcon className="pointer-events-none size-3.5 shrink-0 text-[var(--muted-foreground)]" aria-hidden />
            )}
            <span className="truncate">{item.name}</span>
            {statusLabel ? (
              <span className="shrink-0 text-[10px] uppercase tracking-wide text-[var(--muted-foreground)]">
                {statusLabel}
              </span>
            ) : null}
          </button>
        </div>
        {isFolder && isExpanded && childIds.length > 0 ? (
          <SourceTreeNodes
            sourceTree={sourceTree}
            nodeIds={childIds}
            depth={depth + 1}
            expandedIds={expandedIds}
            selectedNodeId={selectedNodeId}
            onToggleExpanded={onToggleExpanded}
            onNodeSelect={onNodeSelect}
          />
        ) : null}
      </div>
    );
  });
}

function hasTreeDocuments(sourceTree: SourceTreeSnapshot) {
  return Object.values(sourceTree.items).some((item) => item.kind === "document");
}

function formatTreeStatus(status: unknown) {
  if (typeof status !== "string" || !status || status === "ready") return null;
  return status.replace(/_/g, " ");
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
