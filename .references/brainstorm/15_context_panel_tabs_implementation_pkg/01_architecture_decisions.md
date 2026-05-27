# 01 — Architecture and UX Decisions

## Feature summary

Add two tabs to the existing right-hand chat side panel:

```text
Right Panel
├── Context Stream
│   └── Retrieved context/evidence for selected assistant response
└── Source Navigator
    └── Exact source/document context selected from workspace tree
```

The existing side panel already represents retrieved evidence from chat. The new design should preserve that capability while adding deterministic source inspection when a user clicks a source in the workspace tree.

## Key product rule

```text
Chat retrieval populates Context Stream.
Workspace-tree click populates Source Navigator.
```

Do not make workspace-tree clicks automatically rerun retrieval. A source click should be exact navigation/inspection, not semantic search.

## Why the separation matters

Retrieval is probabilistic. Source navigation is deterministic.

If clicking a tree node runs retrieval, the panel may show context related to the node but not necessarily the exact clicked node. That will confuse users. Instead:

- Tree click = exact node context.
- Chat ask = retrieved context stream.
- Evidence click = selected retrieved evidence, optionally with an `Open source` action.

## Panel tab behavior

### Context Stream tab

Purpose: show what the system retrieved for the currently selected assistant message.

Content:

- retrieval summary
- pipeline progress
- retrieved evidence cards
- text/table/figure context items
- errors for the selected retrieval turn

Default activation:

- after a user submits a chat question
- when user clicks/selects an assistant response
- when the system is currently retrieving context

### Source Navigator tab

Purpose: show exact context for a selected workspace-tree node.

Content:

- breadcrumb path
- domain/document metadata
- selected node type: document, section, page, chunk, or asset
- exact text preview or full chunk text
- associated assets if available
- page/section references
- actions: `Open in tree`, `Use as retrieval filter` later, `Copy citation` later

Default activation:

- when user clicks a workspace-tree source node
- when user clicks `Open source` from an evidence item

## First-version scope

Implement now:

- two tabs in `SidePanel.tsx`
- preserve current retrieved-context behavior under `Context Stream`
- add backend endpoint for exact source inspection
- clicking workspace-tree node opens `Source Navigator`
- source navigator supports document, section, page, chunk, and asset nodes
- preserve selected source context while swapping back and forth between tabs
- handle loading, missing node, and permission errors

Defer:

- persistent pinned context
- comments/annotations
- collaborative source selection
- automatic retrieval filters
- full PDF viewer
- streaming source inspection
- direct LightRAG frontend calls

## Frontend state model

Add explicit state fields instead of overloading existing context arrays.

Recommended state:

```ts
type SidePanelTab = "context-stream" | "source-navigator";

type SourceNavigatorState = {
  selectedDomainId?: string;
  selectedNodeId?: string;
  selectedTreeLabel?: string;
  context?: WorkspaceSourceContext;
  loading: boolean;
  error?: string;
};
```

Keep chat retrieval context separate:

```ts
contextByAssistantId: Record<string, AssistantTurnContext>;
selectedAssistantMessageId?: string;
```

Do not store source navigator state inside `AssistantTurnContext`. It is not tied to an assistant response.

## Backend architecture rule

Do not let the frontend call LightRAG directly for source inspection.

Correct flow:

```text
Frontend
  → Context Engine backend
    → local document metadata / parsed structure / asset registry
    → optional LightRAG adapter only if needed later
```

For the first implementation, source inspection should mostly use local document processing structures that already power the workspace tree.

## Permission model

All authenticated users can:

- load the workspace tree for available domains
- inspect readable source nodes
- view retrieved context for their chat turns

Admin-only actions remain separate:

- upload documents
- archive/delete documents
- reindex documents
- manage LightRAG domains

A regular user clicking a node should never mutate global state.

## UX empty states

### Context Stream empty state

```text
No retrieved context yet.
Ask a question or select an assistant response to inspect retrieved evidence.
```

### Source Navigator empty state

```text
No source selected.
Select a document, section, page, chunk, or asset from the workspace tree.
```

### Source Navigator loading state

```text
Loading source context…
```

### Source Navigator missing/error state

```text
Source context is unavailable.
The node may have been deleted, archived, or you may not have access.
```

## Visual recommendation

Use a compact two-button segmented tab control at the top of the side panel rather than adding a new dependency.

```text
┌─────────────────────────────────────┐
│ Context                             ×│
│ [Context Stream] [Source Navigator] │
├─────────────────────────────────────┤
│ tab content...                      │
└─────────────────────────────────────┘
```

The side panel is already resizable, so preserve that behavior.
