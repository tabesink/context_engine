# 03 — Frontend Implementation Plan

## Current frontend anchor points

The current client already includes:

- `client/src/components/chat/SidePanel.tsx` — existing right side panel for retrieved context.
- `client/src/components/chat/WorkspaceTree.tsx` — source tree using `@headless-tree/*`.
- `client/src/components/chat/LightRagChatShell.tsx` — main chat shell, retrieval submit flow, source tree loading, side panel wiring.
- `client/src/stores/chat-session-store.ts` — simple external store for chat messages, context by assistant ID, selected assistant response, source tree, status, and errors.
- `client/src/api/workspace-tree.ts` — fetches backend workspace tree and converts it to `SourceTreeSnapshot`.
- `client/src/lib/retrieve-response-adapter.ts` — adapts backend retrieval evidence into `ContextPanelItem[]`.
- `client/src/types/chat.ts` — chat, context, source-tree, and stream types.

The implementation should extend these files instead of adding a parallel panel system.

## Frontend objective

Refactor the side panel into two tabs:

```text
[Context Stream] [Source Navigator]
```

Context Stream keeps the current retrieved evidence behavior.
Source Navigator shows exact source context selected from the workspace tree.

## Type updates

Modify:

```text
client/src/types/chat.ts
```

Add:

```ts
export type SidePanelTab = "context-stream" | "source-navigator";

export type WorkspaceContextBreadcrumbItem = {
  id?: string | null;
  kind: string;
  title: string;
};

export type WorkspaceContextDocument = {
  document_id: string;
  title: string;
  filename?: string | null;
  content_type?: string | null;
  status?: string | null;
  source_path?: string | null;
};

export type WorkspaceContextAsset = {
  asset_id: string;
  document_id: string;
  asset_type: string;
  title: string;
  caption?: string | null;
  page_number?: number | null;
  section_id?: string | null;
  url?: string | null;
  thumbnail_url?: string | null;
  mime_type?: string | null;
  metadata: Record<string, unknown>;
};

export type WorkspaceSourceContext = {
  node_id: string;
  kind: "domain" | "document" | "section" | "page" | "chunk" | "asset";
  title: string;
  domain_id: string;
  breadcrumb: WorkspaceContextBreadcrumbItem[];
  document?: WorkspaceContextDocument | null;
  section_id?: string | null;
  page_number?: number | null;
  page_start?: number | null;
  page_end?: number | null;
  chunk_id?: string | null;
  asset_id?: string | null;
  summary?: string | null;
  text?: string | null;
  assets: WorkspaceContextAsset[];
  metadata: Record<string, unknown>;
};

export type SourceNavigatorState = {
  selectedDomainId?: string;
  selectedNodeId?: string;
  selectedTreeLabel?: string;
  context?: WorkspaceSourceContext;
  loading: boolean;
  error?: string;
};
```

Update `ContextPanelItem` to include source navigation handle:

```ts
export type ContextPanelItem = {
  ...
  document_id?: string | null;
  reference_id?: string | null;
  workspace_node_id?: string | null;
};
```

## Preserve tree node metadata

Current `fetchWorkspaceTree()` only stores the backend node kind in `handles`. Change it to preserve all useful backend node fields.

Modify:

```text
client/src/api/workspace-tree.ts
```

Expand local type:

```ts
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
  page_start?: number | null;
  page_end?: number | null;
  asset_type?: string | null;
  thumbnail_url?: string | null;
  metadata?: Record<string, unknown>;
};
```

In `walkNode()`:

```ts
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
    page_start: node.page_start ?? null,
    page_end: node.page_end ?? null,
    asset_type: node.asset_type ?? null,
    thumbnail_url: node.thumbnail_url ?? null,
    metadata: node.metadata ?? {},
  },
};
```

## Add source context API client

Add:

```text
client/src/api/workspace-context.ts
```

```ts
import { apiRequest } from "@/lib/api/client";
import type { WorkspaceSourceContext } from "@/types/chat";

export async function fetchWorkspaceSourceContext(
  domainId: string,
  nodeId: string,
): Promise<WorkspaceSourceContext> {
  const params = new URLSearchParams({ node_id: nodeId });
  return apiRequest(
    `/lightrag/domains/${encodeURIComponent(domainId)}/workspace-context?${params.toString()}`,
  );
}
```

## Store updates

Modify:

```text
client/src/stores/chat-session-store.ts
```

Add to `ChatSessionState`:

```ts
sidePanelTab: SidePanelTab;
sourceNavigator: SourceNavigatorState;
```

Default state:

```ts
sidePanelTab: "context-stream",
sourceNavigator: { loading: false },
```

Avoid storing source navigator context inside `contextByAssistantId`. The source navigator is independent from the selected assistant turn.

## WorkspaceTree click behavior

Modify:

```text
client/src/components/chat/WorkspaceTree.tsx
```

Update props:

```ts
type WorkspaceTreeProps = {
  sourceTree?: SourceTreeSnapshot | null;
  selectedNodeId?: string;
  onNodeSelect?: (nodeId: string, item: SourceTreeItem) => void;
};
```

In the rendered tree item:

- add `onClick`
- call `onNodeSelect(item.getId(), item.getItemData())`
- keep expand/collapse behavior for folder icon or whole row; if conflicts appear, use a chevron/row click split

Recommended behavior:

```text
Single click row → select and inspect node
Folder disclosure control → expand/collapse
```

For first implementation, it is acceptable if clicking a folder both expands and selects it, as long as source context still loads.

## LightRagChatShell wiring

Modify:

```text
client/src/components/chat/LightRagChatShell.tsx
```

Add source navigator state readers:

```ts
const sidePanelTab = useChatSessionStore((s) => s.sidePanelTab);
const sourceNavigator = useChatSessionStore((s) => s.sourceNavigator);
```

Add setters:

```ts
const setSidePanelTab = useCallback((sidePanelTab: SidePanelTab) => {
  setChatSessionState({ sidePanelTab });
}, []);
```

Add tree click handler:

```ts
const handleWorkspaceNodeSelect = useCallback(async (nodeId: string, item: SourceTreeItem) => {
  const domainId = getSelectedLightRagDomainId();

  setSidePanelOpen(true);
  setChatSessionState({
    sidePanelTab: "source-navigator",
    sourceNavigator: {
      selectedDomainId: domainId,
      selectedNodeId: nodeId,
      selectedTreeLabel: item.name,
      loading: true,
    },
  });

  try {
    const context = await fetchWorkspaceSourceContext(domainId, nodeId);
    setChatSessionState((current) => ({
      sourceNavigator: {
        ...current.sourceNavigator,
        context,
        loading: false,
        error: undefined,
      },
    }));
  } catch (error) {
    const message = error instanceof Error ? error.message : "Could not load source context.";
    setChatSessionState((current) => ({
      sourceNavigator: {
        ...current.sourceNavigator,
        loading: false,
        error: message,
      },
    }));
  }
}, []);
```

When chat submit begins or selected assistant response changes, set active tab to context stream:

```ts
setChatSessionState({ sidePanelTab: "context-stream" });
```

Do this when:

- user submits a new question
- user selects an assistant message in `ConversationView`

Do not clear source navigator state. Users should be able to return to the tab.

## SidePanel refactor

Modify:

```text
client/src/components/chat/SidePanel.tsx
```

New props:

```ts
type SidePanelProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  activeTab: SidePanelTab;
  onActiveTabChange: (tab: SidePanelTab) => void;
  contextItems: ContextPanelItem[];
  sourceNavigator: SourceNavigatorState;
  onOpenSourceFromContext?: (nodeId: string) => void;
  ...existing props
};
```

Render:

```tsx
<header>
  <h2>Context</h2>
  <button onClick={onClose}>...</button>
</header>

<div role="tablist">
  <button role="tab" aria-selected={activeTab === "context-stream"}>Context Stream</button>
  <button role="tab" aria-selected={activeTab === "source-navigator"}>Source Navigator</button>
</div>

{activeTab === "context-stream" ? (
  <ContextStreamTab ... />
) : (
  <SourceNavigatorTab sourceNavigator={sourceNavigator} />
)}
```

Keep the current panel resizing and responsive/mobile overlay behavior.

## SourceNavigatorTab component

Can be internal to `SidePanel.tsx` first, then extracted later if it grows.

Render states:

1. loading
2. error
3. empty
4. loaded context

Loaded layout:

```text
Breadcrumb
Document title / node type
Summary
Text
Assets
Metadata chips
```

Recommended card structure:

```tsx
function SourceNavigatorTab({ sourceNavigator }: { sourceNavigator: SourceNavigatorState }) {
  if (sourceNavigator.loading) return <LoadingBlock />;
  if (sourceNavigator.error) return <ErrorBlock message={sourceNavigator.error} />;
  if (!sourceNavigator.context) return <EmptySourceNavigator />;

  const context = sourceNavigator.context;
  return (
    <div className="space-y-4">
      <Breadcrumb items={context.breadcrumb} />
      <section>
        <p className="text-xs uppercase tracking-wide text-[var(--muted-foreground)]">
          {context.kind}
        </p>
        <h3>{context.title}</h3>
        {context.document ? <p>{context.document.title}</p> : null}
      </section>
      {context.summary ? <SummaryBlock>{context.summary}</SummaryBlock> : null}
      {context.text ? <SourceText text={context.text} /> : <NoText />}
      {context.assets.length ? <SourceAssets assets={context.assets} /> : null}
    </div>
  );
}
```

## Context Stream improvements

Keep current behavior but add an `Open source` action on evidence cards when `workspace_node_id` is available.

In `retrieve-response-adapter.ts`, map backend `workspace_node_id`:

```ts
workspace_node_id: item.workspace_node_id ?? inferWorkspaceNodeId(item),
```

Fallback inference:

```ts
function inferWorkspaceNodeId(item: RetrieveEvidence) {
  if (item.chunk_id) return `chunk:${item.document_id}:${item.chunk_id}`;
  if (item.page_start) return `page:${item.document_id}:${item.page_start}`;
  return item.document_id ? `document:${item.document_id}` : null;
}
```

In `TextContextItem`, show:

```tsx
{item.workspace_node_id ? (
  <button onClick={() => onOpenSourceFromContext?.(item.workspace_node_id!)}>
    Open source
  </button>
) : null}
```

That should switch to Source Navigator and fetch the exact source context.

## Manual UX checks

1. Load chat page.
2. Confirm right panel defaults to Context Stream.
3. Ask a question.
4. Confirm retrieved evidence appears in Context Stream.
5. Click a workspace-tree document.
6. Confirm Source Navigator tab activates and loads exact source.
7. Switch back to Context Stream.
8. Confirm retrieved context remains.
9. Click `Open source` from an evidence card.
10. Confirm Source Navigator loads matching chunk/page/document.
11. Confirm tree click does not rerun chat retrieval.
12. Confirm mobile side panel opens when tree node is selected.

## Design notes

Use the existing flat/lean visual grammar:

- subtle borders
- compact text
- muted metadata chips
- minimal panel controls
- no heavy card nesting
- no bright color unless status/error/action requires it

