# Context Engine Lean Refactor Review

Generated: 2026-05-27  
Repo reviewed: `https://github.com/tabesink/context_engine.git`  
Review mode: GitHub web/raw inspection. The execution environment could not clone the repo because DNS resolution for `github.com` failed, so patches are provided as reviewable `.diff` files rather than applied commits.

```text
Attempted command:
mkdir -p /mnt/data/context_engine_review
cd /mnt/data/context_engine_review
git clone https://github.com/tabesink/context_engine.git

Result:
fatal: unable to access 'https://github.com/tabesink/context_engine.git/': Could not resolve host: github.com
```

## Executive Summary

The codebase is close to the intended architecture, but the recent right-panel/source-navigation work is only partially integrated.

The largest issue is not duplicated implementation; it is an incomplete bridge:

- Backend has `WorkspaceContextService` and tests for deterministic source inspection.
- Backend has `WorkspaceSourceContext` schema.
- Backend has `WorkspaceTreeService` and a workspace-tree route.
- But `app/main.py` does not include a workspace-context route, and `app/api/routes/` does not currently list one.
- Frontend has a right `SidePanel`, but it is still a Context Stream panel only. It has no explicit Context Stream / Source Navigator tab state.
- Frontend `WorkspaceTree` is display-only. It does not surface node selection to the panel.
- Retrieval assets are returned by the backend, but the retrieve-response adapter does not attach them to context cards and the panel still renders table/figure placeholders.

The safest lean path is:

1. Expose existing `WorkspaceContextService` through one small backend route.
2. Add one frontend source-context API client and one `sourceNavigator` state slice.
3. Split `SidePanel` into a shell plus two content views.
4. Introduce one shared `AssetCards` component for table/figure cards.
5. Centralize backend asset URL construction in one tiny helper.

Do not build a second source navigator. Do not make tree clicks trigger retrieval. Do not make frontend parse raw metadata as the stable display contract.

---

## Deliverable 1 — Architecture Map

### 1. App bootstrap and route surface

| Flow | Owner module | Input contract | Output contract | Type |
|---|---|---|---|---|
| FastAPI app setup | `app/main.py` | Runtime settings | FastAPI app with routers | Infrastructure |
| Active routes | `app/api/routes/*` | HTTP requests | JSON/File responses | Mixed |

Current active routers include health, auth, documents, admin, ai settings, retrieve, lightrag, lightrag admin, users, workspace tree, and jobs. There is no visible `workspace_context` router in `app/main.py` or the route directory listing.

### 2. Semantic retrieval flow

| Step | Owner | Input | Output | Deterministic navigation or semantic retrieval? |
|---|---|---|---|---|
| HTTP route | `app/api/routes/retrieve.py` | `RetrieveRequest` | `RetrieveResponse` | Semantic retrieval |
| Orchestration | `app/services/retrieval_service.py` | request + user | `RetrievalResult` then API response | Semantic retrieval |
| Domain validation | `LightRAGDomainRegistry` | `lightrag_domain_id` | available domain or HTTP error | Safety gate |
| Routing | `RetrievalRoutingPolicy` | mode | `RetrievalBackend` | Policy |
| Remote semantic engine | `LightRAGRemoteRetrievalEngine` | query/mode/top_k/domain | evidence list | Semantic retrieval |
| LightRAG boundary | `LightRAGRemoteAdapter.for_domain()` | domain id | HTTP client to registered domain | Backend-only remote boundary |
| Evidence mapping | `app/retrieval/evidence_mapper.py` | domain `Evidence` | `EvidenceResponse` | Display contract mapping |
| Asset enrichment | `app/services/retrieval_asset_resolver.py` | evidence + repository | list of `AssetResponse` | Display enrichment |

Notes:

- Semantic retrieval is correctly backend-mediated. The frontend calls `/retrieve`, not LightRAG directly.
- The backend `RetrieveResponse` already has stable fields for `source_path`, `document_title`, `chunk_id`, and `reference_id`.
- Missing stable field: `workspace_node_id` on evidence.
- Missing display linkage: returned `assets` are top-level response assets, not associated with individual `ContextPanelItem` cards on the frontend.

### 3. Workspace tree flow

| Step | Owner | Input | Output | Deterministic navigation or semantic retrieval? |
|---|---|---|---|---|
| HTTP route | `app/api/routes/workspace_tree.py` | `domain_id`, `depth`, `include_assets` | `WorkspaceTreeResponse` | Deterministic navigation |
| Service | `WorkspaceTreeService` | domain/user/depth/assets flag | domain/document/section/page/chunk/asset tree | Deterministic navigation |
| Repositories | `DocumentRepository`, `DocumentProcessingRepository` | readable docs + processed structure | document structures/assets/chunks | Storage access |
| Frontend API | `client/src/api/workspace-tree.ts` | domain id | `SourceTreeSnapshot` | Deterministic navigation display |
| Frontend view | `WorkspaceTree.tsx` | `SourceTreeSnapshot` | tree UI | Display-only today |

Notes:

- Backend is the right source of truth for tree shape.
- Frontend flattens the backend tree into a `SourceTreeSnapshot`, but drops most stable node fields such as `document_id`, `chunk_id`, `asset_id`, `page_number`, and `thumbnail_url`.
- `WorkspaceTree` currently appears display-only. It needs one `onSelectNode(nodeId)` prop, not retrieval mutation.

### 4. Workspace source context flow

| Step | Owner | Input | Output | Deterministic navigation or semantic retrieval? |
|---|---|---|---|---|
| Schema | `app/schemas/workspace_context.py` | source node kind/context | `WorkspaceSourceContext` | Deterministic navigation |
| Service | `app/services/workspace_context_service.py` | `domain_id`, `node_id`, user | exact context for selected domain/document/section/page/chunk/asset | Deterministic navigation |
| Tests | `tests/test_workspace_context_service.py` | fake domain/document/structure | service behavior assertions | Deterministic navigation |
| Missing route | `app/api/routes/workspace_context.py` | should accept `domain_id` + `node_id` | should return `WorkspaceSourceContext` | Missing integration |
| Missing frontend client | `client/src/api/source-context.ts` | should fetch source context | should return `WorkspaceSourceContext` | Missing integration |
| Missing panel view | `SourceNavigatorView` | selected source context | exact source display with assets | Missing integration |

This is the highest-value small patch. The service exists, so do not create a parallel service.

### 5. Right-panel frontend state flow

| Step | Owner | Current state | Target state |
|---|---|---|---|
| Retrieval context state | `chat-session-store.ts` | `contextByAssistantId`, `selectedAssistantMessageId`, `progressByAssistantId` | Keep as Context Stream state |
| Workspace tree state | `chat-session-store.ts` | global `sourceTree` and per-assistant `sourceTree` copy | Prefer global source tree; avoid per-turn tree unless explicitly needed |
| Panel shell | `SidePanel.tsx` | single “Context” panel | Shell with explicit `activeTab: context-stream | source-navigator` |
| Source selection state | missing | none | `selectedSourceNodeId`, `sourceContext`, `sourceContextStatus`, `sourceContextError` |
| Tree click behavior | `WorkspaceTree.tsx` | display only | call `onSelectNode(nodeId)`; no retrieval; no filter mutation |

### 6. Asset/image/table rendering flow

| Step | Owner | Current state | Target state |
|---|---|---|---|
| Backend asset endpoints | `app/api/routes/documents.py` | `/documents/{document_id}/assets/{asset_id}` and thumbnail route | Keep |
| Retrieval asset enrichment | `RetrievalAssetResolver` | top-level assets on retrieval response | Keep, but expose frontend-friendly `VisualAsset` type |
| Workspace tree assets | `WorkspaceTreeService` | asset nodes have `thumbnail_url` and metadata URL | Use centralized backend asset URL helper |
| Workspace source context assets | `WorkspaceContextService` | assets returned with URL/thumbnail URL | Use same centralized helper |
| Frontend rendering | `SidePanel.tsx` | placeholder figure/table cards | One reusable `AssetCards` component |

### 7. LightRAG boundary

| Concern | Current assessment |
|---|---|
| Frontend direct LightRAG calls | No direct LightRAG base URL calls observed in inspected frontend API files. Graph APIs call Context Engine `/lightrag/domains/{domainId}/...`, which is acceptable. |
| Backend remote boundary | `LightRAGRemoteAdapter.for_domain()` resolves registered domains and calls LightRAG from backend. |
| Semantic fallback | Local retrieval exists in code, but product direction says local navigation only. Keep naming clear: local retrieval must not become semantic fallback. |

---

## Deliverable 2 — Duplication and Bloat Audit

| Area | Problem | Evidence/File Paths | Risk | Recommendation | Patch Size |
|---|---|---|---|---|---|
| Workspace source context route | `WorkspaceContextService` exists and is tested, but no route is registered/exposed. | `app/services/workspace_context_service.py`, `app/schemas/workspace_context.py`, `tests/test_workspace_context_service.py`, `app/main.py`, `app/api/routes/` | Frontend may implement source context itself or misuse tree/retrieval APIs. | Add one `app/api/routes/workspace_context.py` and include it in `app/main.py`. | Small |
| Right panel architecture | `SidePanel` is one Context panel, not a two-tab shell. | `client/src/components/chat/SidePanel.tsx` | Source Navigator will be bolted into Context Stream or duplicate a panel. | Convert `SidePanel` into shell + `ContextStreamView` + `SourceNavigatorView`. | Medium |
| Asset card rendering | Table and figure rendering are placeholder functions inside `SidePanel`; no reusable asset cards. | `SidePanel.tsx` has `TableContextItem`, `FigureContextItem`. | Table/figure cards will diverge visually and behaviorally. | Extract one `AssetCards` component using a shared `VisualAsset` type. | Small/Medium |
| Retrieval asset linkage | Backend returns assets, but frontend adapter only counts them in the summary and does not attach them to cards. | `RetrieveResponse.assets`; `adaptRetrieveResponse()` | Retrieved images/tables never show in the panel even when backend sends them. | Add `assets` to `ContextPanelItem` or add `visualAssetsByContextItemId`; prefer `assets` on item. | Small |
| Asset URL construction | Asset URLs are built in several backend places. | `WorkspaceTreeService._asset_node`, `WorkspaceContextService._asset_payload`, `RetrievalAssetResolver.resolve` | Drift between table/figure asset URLs, thumbnail behavior, and security expectations. | Add tiny helper: `asset_url(document_id, asset_id)` and `asset_thumbnail_url(...)`. | Small |
| Workspace tree frontend contract | Frontend tree adapter drops stable backend fields into only `handles.node_kind`. | `client/src/api/workspace-tree.ts` | Source Navigator will need raw metadata or node-id parsing instead of stable fields. | Preserve node IDs and useful fields in `SourceTreeItem.handles` or create `WorkspaceTreeNode` type shared in frontend. | Small |
| Workspace node parsing | Backend has `parse_workspace_node_id`, but frontend has no source-context client and no typed selected node flow. | `WorkspaceContextService.parse_workspace_node_id`, `WorkspaceTree.tsx` | Frontend may parse node IDs ad hoc. | Keep parsing server-side. Frontend passes opaque `node_id`. | Small |
| State separation | Chat context, source tree, selected assistant, and panel open state are present, but source selection/tab state is absent. | `chat-session-store.ts`, `LightRagChatShell.tsx` | Selected assistant message may get overloaded as selected source. | Add explicit `activePanelTab`, `selectedSourceNodeId`, `sourceContext*` state. | Medium |
| Per-turn source tree copy | `AssistantTurnContext` contains `sourceTree`, while global `sourceTree` also exists. | `types/chat.ts`, `LightRagChatShell.tsx` | Duplicate state; stale tree can differ from current workspace tree. | Keep global tree as source of truth unless historical tree snapshots are a deliberate feature. | Small |
| CLI/TUI tests | README says CLI/TUI is deprecated, but many CLI tests remain in active test tree. | `README.md`, `tests/test_cli_*` | Legacy workflows can keep imports/packaging alive and slow refactors. | Keep for now, but mark as legacy or move to a legacy test marker. | Small/Medium |
| Frontend API placement | Retrieval API is under `client/src/lib/api/retrieve.ts`, workspace tree is under `client/src/api/workspace-tree.ts`. | `client/src/api`, `client/src/lib/api` | API clients are split by convention, increasing drift. | Normalize new source-context client under `client/src/api/`; later migrate retrieval client if desired. | Small |

---

## Deliverable 3 — Lean Target Architecture

### Backend

```text
app/api/routes/retrieve.py
  -> RetrievalService
     -> LightRAGDomainRegistry
     -> RetrievalRoutingPolicy
     -> LightRAGRemoteRetrievalEngine
        -> LightRAGRemoteAdapter.for_domain(domain_id)
     -> evidence_mapper.to_evidence_response()
     -> RetrievalAssetResolver

app/api/routes/workspace_tree.py
  -> WorkspaceTreeService
     -> DocumentAccessPolicy
     -> DocumentRepository
     -> DocumentProcessingRepository

app/api/routes/workspace_context.py       [add]
  -> WorkspaceContextService              [already exists]
     -> DocumentAccessPolicy
     -> DocumentRepository
     -> DocumentProcessingRepository
```

### Frontend

```text
LightRagChatShell
  state:
    Context Stream:
      selectedAssistantMessageId
      contextByAssistantId
      progressByAssistantId
    Source Navigator:
      selectedSourceNodeId
      sourceContext
      sourceContextStatus
      sourceContextError
    Shared:
      activePanelTab
      sourceTree

  children:
    WorkspaceTree(onSelectNode)
    SidePanel(activeTab)
      ContextStreamView
      SourceNavigatorView
        AssetCards
```

### Contract target

```ts
type VisualAsset = {
  asset_id: string;
  document_id: string;
  asset_type: "figure" | "table" | string;
  title?: string | null;
  caption?: string | null;
  page_number?: number | null;
  url?: string | null;
  thumbnail_url?: string | null;
  mime_type?: string | null;
};

type ContextPanelItem = {
  id: string;
  kind: "text" | "table" | "figure";
  title: string;
  content: string;
  source_path?: string | null;
  document_title?: string | null;
  document_id?: string | null;
  workspace_node_id?: string | null;
  chunk_id?: string | null;
  reference_id?: string | null;
  assets?: VisualAsset[];
  metadata?: Record<string, unknown>;
};
```

---

## Deliverable 4 — Phased Refactor Plan

### Phase 0 — Safety

Commands to run in a normal dev environment:

```bash
python -m pytest -q
cd client && npm run lint && npm run build
```

Capture failures before patching. Do not mix build fixes with panel/source refactor unless unavoidable.

### Phase 1 — Remove obvious duplication

1. Add backend asset URL helper.
2. Replace repeated URL strings in:
   - `WorkspaceTreeService._asset_node`
   - `WorkspaceContextService._asset_payload`
   - `RetrievalAssetResolver.resolve`
3. Extract frontend `AssetCards` from `SidePanel` placeholder rendering.
4. Extract repeated empty/loading/error states into tiny panel primitives if duplication grows during tab split.

### Phase 2 — Stabilize contracts

1. Add `workspace_node_id` to `EvidenceResponse` using a deterministic helper:
   - `chunk:{document_id}:{chunk_id}` when chunk id exists.
   - `document:{document_id}` fallback.
2. Add assets to `ContextPanelItem` frontend type.
3. Make `adaptRetrieveResponse()` attach relevant top-level response assets to context items where possible.
4. Keep raw `metadata` available, but do not require frontend to parse it for core display.

### Phase 3 — Simplify state

1. Add `activePanelTab` to chat/session state.
2. Add source navigator state:
   - `selectedSourceNodeId`
   - `sourceContext`
   - `sourceContextStatus`
   - `sourceContextError`
3. Wire `WorkspaceTree` clicks:
   - Set selected node.
   - Set tab to Source Navigator.
   - Fetch `/lightrag/domains/{domain_id}/workspace-context?node_id={node_id}`.
   - Do **not** call retrieval.
   - Do **not** mutate retrieval filters.

### Phase 4 — Tests

Backend:

- Existing `test_workspace_context_service.py` is good.
- Add route-level test for `GET /lightrag/domains/{domain_id}/workspace-context`.
- Add evidence mapper test for `workspace_node_id`.
- Add asset URL helper test.

Frontend:

- Run `npm run lint` and `npm run build`.
- If component tests already exist, add one test that a tree click calls source-context client and switches panel tab without mutating retrieval settings.

---

## Deliverable 5 — Proposed Safe Patches

Because the repo could not be cloned in this environment, I prepared patch files rather than applying them. They are included in the downloadable package.

Recommended application order:

1. `patches/0001-wire-workspace-context-route.diff`
2. `patches/0002-centralize-asset-url-helpers.diff`
3. `patches/0003-add-source-context-frontend-types-and-client.diff`
4. `patches/0004-split-right-panel-followup-outline.md`

Patch 0001 is the safest and highest-value patch. It exposes an already-tested service and avoids creating a parallel source-context implementation.

---

## Deliverable 6 — Final Report

### 1. Summary of what changed

No live repo changes were applied because the execution environment could not clone GitHub. Proposed patches were generated as reviewable `.diff` files.

### 2. Files proposed for modification

Backend:

- `app/main.py`
- `app/api/routes/workspace_context.py` — new
- `app/services/asset_urls.py` — new
- `app/services/workspace_tree_service.py`
- `app/services/workspace_context_service.py`
- `app/services/retrieval_asset_resolver.py`
- `app/schemas/retrieval.py`
- `app/retrieval/evidence_mapper.py`

Frontend:

- `client/src/api/source-context.ts` — new
- `client/src/types/chat.ts`
- `client/src/api/workspace-tree.ts`
- `client/src/components/chat/WorkspaceTree.tsx`
- `client/src/components/chat/SidePanel.tsx`
- `client/src/components/chat/AssetCards.tsx` — new
- `client/src/components/chat/LightRagChatShell.tsx`

Tests:

- `tests/test_workspace_context_api.py` — new
- `tests/test_asset_urls.py` — new
- `tests/test_evidence_mapper.py` — update

### 3. Files deleted

None recommended in the first pass. Do not delete CLI/TUI yet; mark/move legacy tests first.

### 4. Duplications removed by proposed patches

- Asset URL construction centralized.
- Workspace context uses the existing service rather than a new frontend/backend implementation.
- Frontend source context gets one API client.
- Right panel target avoids duplicate panel implementations by splitting a shell into two views.

### 5. Remaining technical debt

- `client/src/api` and `client/src/lib/api` are both used for API clients.
- Source tree frontend type currently loses backend node fields.
- Context Stream still lacks real asset rendering.
- `contextByAssistantId` stores `sourceTree`; decide if historical tree snapshots are needed.
- Deprecated CLI/TUI tests still sit in active test suite.

### 6. Risks

- Adding the workspace-context route exposes exact source text and assets; existing `DocumentAccessPolicy` is used, but route-level tests should verify user-read boundaries.
- Centralizing asset URLs must preserve route strings exactly to avoid breaking existing asset links.
- Adding `workspace_node_id` changes response shape by extension only; it should be backward-compatible.
- Frontend panel split can become a UI refactor if not constrained. Keep styling untouched except necessary tab controls.

### 7. Tests run and results

Tests were not run because the repo could not be cloned. Required local validation:

```bash
python -m pytest -q
cd client && npm run lint && npm run build
```

### 8. Recommended next feature implementation path

Implement in this order:

1. Route existing `WorkspaceContextService`.
2. Add frontend source-context client and explicit source navigator state.
3. Wire `WorkspaceTree` click to Source Navigator only.
4. Extract `AssetCards` and render both retrieval assets and source-context assets.
5. Only after this cleanup, add image/table-specific UI refinements.

