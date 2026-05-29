"use client";

import { FileIcon, FolderIcon, FolderOpenIcon } from "lucide-react";
import { hotkeysCoreFeature, syncDataLoaderFeature } from "@headless-tree/core";
import { useTree } from "@headless-tree/react";
import { Tree, TreeItem, TreeItemLabel } from "@/components/reui/tree";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { LightRagDomain, SourceTreeItem, SourceTreeSnapshot } from "@/types/chat";

const emptyTree: SourceTreeSnapshot = {
  root_id: "root",
  items: {
    root: { name: "Root", children: ["workspace"] },
    workspace: { name: "Workspace", children: [] },
  },
  expanded_item_ids: ["workspace"],
};

const indent = 20;

type WorkspaceTreeProps = {
  sourceTree?: SourceTreeSnapshot | null;
  selectedNodeId?: string;
  onNodeSelect?: (nodeId: string, item: SourceTreeItem) => void;
  domains?: LightRagDomain[];
  selectedDomainPort?: number;
  domainsLoading?: boolean;
  onDomainChange?: (port: number) => void;
};

export function WorkspaceTree({
  sourceTree,
  selectedNodeId,
  onNodeSelect,
  domains = [],
  selectedDomainPort,
  domainsLoading = false,
  onDomainChange,
}: WorkspaceTreeProps) {
  const data = normalizeSourceTree(sourceTree);
  const revision = sourceTreeRevision(data);
  const healthyDomains = domains.filter((domain) => domain.is_healthy === true);
  const selectedValue = selectedDomainPort ? String(selectedDomainPort) : undefined;

  return (
    <WorkspaceTreeContent
      key={revision}
      sourceTree={data}
      selectedNodeId={selectedNodeId}
      onNodeSelect={onNodeSelect}
      domains={healthyDomains}
      selectedDomainPortValue={selectedValue}
      domainsLoading={domainsLoading}
      onDomainChange={onDomainChange}
    />
  );
}

function WorkspaceTreeContent({
  sourceTree,
  selectedNodeId,
  onNodeSelect,
  domains,
  selectedDomainPortValue,
  domainsLoading,
  onDomainChange,
}: {
  sourceTree: SourceTreeSnapshot;
  selectedNodeId?: string;
  onNodeSelect?: (nodeId: string, item: SourceTreeItem) => void;
  domains: LightRagDomain[];
  selectedDomainPortValue?: string;
  domainsLoading: boolean;
  onDomainChange?: (port: number) => void;
}) {
  const data = sourceTree;
  const tree = useTree<SourceTreeItem>({
    initialState: {
      expandedItems: data.expanded_item_ids ?? ["workspace"],
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

  return (
    <div className="w-full bg-transparent">
      <div className="mb-3">
        <div className="flex items-center gap-1">
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--muted-foreground)]">Knowledge Base</p>
          <Select
            value={selectedDomainPortValue}
            disabled={domainsLoading || domains.length === 0 || !onDomainChange}
            onValueChange={(value) => onDomainChange?.(Number(value))}
          >
            <SelectTrigger
              size="sm"
              className="size-6 rounded-md border border-transparent bg-transparent p-0 text-[var(--muted-foreground)] shadow-none hover:text-[var(--foreground)] data-[state=open]:border-transparent data-[state=open]:shadow-none [&_svg]:size-3.5 [&_svg]:-rotate-90 [&_svg]:opacity-100"
              aria-label="Select knowledge base domain"
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent
              position="popper"
              side="right"
              align="start"
              sideOffset={0}
              className="rounded-md border-[var(--border)] shadow-none data-[side=right]:translate-x-0"
            >
              {domains.map((domain) => (
                <SelectItem key={domain.domain_id} value={String(domain.port)}>
                  {domain.workspace}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
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
