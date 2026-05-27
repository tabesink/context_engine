# 07 — Junior Developer Checklist

## Phase 0 — Read the current files

Read these backend files:

- [ ] `app/main.py`
- [ ] `app/api/routes/workspace_tree.py`
- [ ] `app/schemas/workspace_tree.py`
- [ ] `app/services/workspace_tree_service.py`
- [ ] `app/schemas/retrieval.py`
- [ ] `app/retrieval/evidence_mapper.py`
- [ ] `app/services/retrieval_service.py`

Read these frontend files:

- [ ] `client/src/components/chat/SidePanel.tsx`
- [ ] `client/src/components/chat/WorkspaceTree.tsx`
- [ ] `client/src/components/chat/LightRagChatShell.tsx`
- [ ] `client/src/stores/chat-session-store.ts`
- [ ] `client/src/types/chat.ts`
- [ ] `client/src/api/workspace-tree.ts`
- [ ] `client/src/lib/retrieve-response-adapter.ts`
- [ ] `client/src/lib/api/retrieve.ts`

## Phase 1 — Backend schema

- [ ] Create `app/schemas/workspace_context.py`.
- [ ] Add breadcrumb item schema.
- [ ] Add document summary schema.
- [ ] Add asset schema.
- [ ] Add `WorkspaceSourceContext` schema.

## Phase 2 — Backend service

- [ ] Create `app/services/workspace_context_service.py`.
- [ ] Add node ID parser.
- [ ] Add domain validation using `LightRAGDomainRegistry`.
- [ ] Add document lookup helper.
- [ ] Add document access check using `DocumentAccessPolicy`.
- [ ] Add document-domain match validation.
- [ ] Add document node builder.
- [ ] Add section node builder.
- [ ] Add page node builder.
- [ ] Add chunk node builder.
- [ ] Add asset node builder.
- [ ] Add shared asset response helper.
- [ ] Add shared breadcrumb helper.

## Phase 3 — Backend route

- [ ] Modify `app/api/routes/workspace_tree.py`.
- [ ] Import new schema and service.
- [ ] Add `GET /{domain_id}/workspace-context` route.
- [ ] Use `node_id: str = Query(..., min_length=1)`.
- [ ] Use the same auth/session/domain-registry dependencies as workspace tree.
- [ ] Convert domain registry errors using existing helper.

## Phase 4 — Retrieval evidence node IDs

- [ ] Add optional `workspace_node_id` to `EvidenceResponse` in `app/schemas/retrieval.py`.
- [ ] Update `app/retrieval/evidence_mapper.py`.
- [ ] Prefer `metadata["workspace_node_id"]`.
- [ ] Fallback to `chunk:{document_id}:{chunk_id}`.
- [ ] Fallback to `page:{document_id}:{page_start}`.
- [ ] Fallback to `document:{document_id}`.
- [ ] Add/update tests.

## Phase 5 — Frontend types

- [ ] Update `client/src/types/chat.ts`.
- [ ] Add `SidePanelTab`.
- [ ] Add source-context types.
- [ ] Add `SourceNavigatorState`.
- [ ] Add optional `workspace_node_id` to `ContextPanelItem`.
- [ ] Update retrieve API type to include `workspace_node_id`.

## Phase 6 — Frontend API client

- [ ] Create `client/src/api/workspace-context.ts`.
- [ ] Add `fetchWorkspaceSourceContext(domainId, nodeId)`.
- [ ] Use `URLSearchParams` for `node_id`.

## Phase 7 — Preserve workspace-tree handles

- [ ] Modify `client/src/api/workspace-tree.ts`.
- [ ] Expand `WorkspaceTreeNode` type.
- [ ] Preserve document/page/chunk/asset fields in `handles`.

## Phase 8 — Store state

- [ ] Modify `client/src/stores/chat-session-store.ts`.
- [ ] Add `sidePanelTab`.
- [ ] Add `sourceNavigator`.
- [ ] Initialize `sidePanelTab` to `context-stream`.
- [ ] Initialize `sourceNavigator` to `{ loading: false }`.

## Phase 9 — SidePanel tabs

- [ ] Modify `client/src/components/chat/SidePanel.tsx`.
- [ ] Add active tab props.
- [ ] Add tab buttons.
- [ ] Move existing content into `ContextStreamTab`.
- [ ] Add `SourceNavigatorTab`.
- [ ] Preserve resize logic.
- [ ] Preserve mobile overlay behavior.

## Phase 10 — WorkspaceTree click wiring

- [ ] Modify `client/src/components/chat/WorkspaceTree.tsx`.
- [ ] Add `onNodeSelect` prop.
- [ ] Add `selectedNodeId` prop.
- [ ] Highlight selected node.
- [ ] Call `onNodeSelect` on row click.

## Phase 11 — Shell integration

- [ ] Modify `client/src/components/chat/LightRagChatShell.tsx`.
- [ ] Import source-context API.
- [ ] Read `sidePanelTab` and `sourceNavigator` from store.
- [ ] Pass active tab props to `SidePanel`.
- [ ] Add `handleWorkspaceNodeSelect`.
- [ ] Pass handler to `WorkspaceTree`.
- [ ] Set tab to Context Stream on chat submit.
- [ ] Set tab to Context Stream on assistant message select.
- [ ] Open panel and set tab to Source Navigator on tree click.

## Phase 12 — Evidence Open Source action

- [ ] Update `client/src/lib/retrieve-response-adapter.ts` to include `workspace_node_id`.
- [ ] Add fallback inference.
- [ ] Add `Open source` button to context item card when available.
- [ ] Wire it to the same source navigator fetch flow.

## Phase 13 — Test and verify

Backend:

- [ ] Run backend tests.
- [ ] Add missing tests if needed.

Frontend:

- [ ] `cd client && npm run lint`
- [ ] `cd client && npm run build`

Manual:

- [ ] Ask chat question and verify Context Stream.
- [ ] Click tree source and verify Source Navigator.
- [ ] Switch tabs and verify state persists.
- [ ] Verify tree click does not rerun retrieval.
- [ ] Verify evidence `Open source` works.
