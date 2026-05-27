# 06 — Coding Agent Prompt

Use this prompt with a coding agent.

---

You are a senior full-stack engineer working in the `tabesink/context_engine` repository.

## Goal

Implement a two-tab right-hand panel in the chat UI:

1. **Context Stream** — existing retrieved context/evidence for the selected assistant message.
2. **Source Navigator** — exact source context when the user clicks a workspace-tree node.

The existing side panel already shows retrieved context from chat. Preserve that behavior. Add deterministic source inspection as a second tab.

## Required UX behavior

- Chat retrieval populates the `Context Stream` tab.
- Clicking a workspace-tree source node opens the `Source Navigator` tab.
- A workspace-tree click must not silently rerun retrieval.
- A workspace-tree click must not silently set a retrieval filter.
- Switching tabs should preserve the latest content in each tab.
- Evidence items in the Context Stream should expose an `Open source` action when a `workspace_node_id` is available.

## Backend work

Inspect current files first:

- `app/main.py`
- `app/api/routes/workspace_tree.py`
- `app/schemas/workspace_tree.py`
- `app/services/workspace_tree_service.py`
- `app/schemas/retrieval.py`
- `app/retrieval/evidence_mapper.py`
- `app/storage/repositories/document_processing.py`
- `app/storage/repositories/documents.py`
- `app/services/document_access_policy.py`
- `app/services/lightrag_domain_registry.py`

Add:

- `app/schemas/workspace_context.py`
- `app/services/workspace_context_service.py`

Add endpoint in `app/api/routes/workspace_tree.py`:

```http
GET /lightrag/domains/{domain_id}/workspace-context?node_id=<node_id>
```

This endpoint should return display-ready source context for node kinds:

- domain
- document
- section
- page
- chunk
- asset

Use existing repositories and access policy. Validate that a document belongs to the selected LightRAG domain. Do not expose inaccessible documents. Do not call LightRAG directly from the frontend.

Also update retrieval evidence response to include:

```py
workspace_node_id: str | None = None
```

Map it in `app/retrieval/evidence_mapper.py` using metadata first, then chunk/page/document fallback.

## Frontend work

Inspect current files first:

- `client/src/components/chat/SidePanel.tsx`
- `client/src/components/chat/WorkspaceTree.tsx`
- `client/src/components/chat/LightRagChatShell.tsx`
- `client/src/stores/chat-session-store.ts`
- `client/src/types/chat.ts`
- `client/src/api/workspace-tree.ts`
- `client/src/lib/retrieve-response-adapter.ts`
- `client/src/lib/api/retrieve.ts`

Add:

- `client/src/api/workspace-context.ts`

Update types:

- `SidePanelTab = "context-stream" | "source-navigator"`
- `WorkspaceSourceContext`
- `SourceNavigatorState`
- add optional `workspace_node_id` to retrieved/evidence context item types

Update `SidePanel.tsx`:

- preserve resize/mobile behavior
- add two-tab header
- move existing retrieved-context content into `ContextStreamTab`
- add `SourceNavigatorTab`

Update `WorkspaceTree.tsx`:

- add `onNodeSelect`
- preserve backend node details in `handles`
- call `onNodeSelect(nodeId, itemData)` on row click

Update `LightRagChatShell.tsx`:

- maintain `sidePanelTab`
- maintain `sourceNavigator` state
- on chat submit, activate `Context Stream`
- on assistant select, activate `Context Stream`
- on workspace-tree click, activate `Source Navigator`, open panel, fetch source context
- do not clear retrieved context when source navigator is used

Update retrieval adapter:

- include `workspace_node_id` in `ContextPanelItem`
- fallback infer node ID from `chunk_id`, `page_start`, or `document_id`

## Implementation constraints

- Keep changes lean and local.
- Do not add a new state-management library.
- Do not add a new tabs dependency unless existing UI primitives already include one.
- Do not create a second side panel.
- Do not make frontend call LightRAG APIs directly.
- Do not make source click mutate global retrieval scope.

## Tests and checks

Backend:

- add tests for source context service and endpoint
- test invalid node IDs, missing nodes, access control, cross-domain rejection
- test retrieval mapper `workspace_node_id`

Frontend:

- run `npm run lint`
- run `npm run build`
- manually verify chat retrieval still populates Context Stream
- manually verify tree clicks populate Source Navigator

## Definition of done

The right panel has two tabs. Chat retrieval displays in Context Stream. Workspace-tree clicks display exact source context in Source Navigator. Both states are preserved while swapping tabs. The backend endpoint enforces auth, domain availability, document-domain matching, and document access policy.
