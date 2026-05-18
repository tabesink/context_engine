# Lean LightRAG Integration Plan

## Objective

`context_engine` uses an external LightRAG service for optional:

- admin-only document ingestion forwarding
- semantic/context retrieval
- graph visualization data

The implementation stays HTTP-only. Do not copy LightRAG internals into `app/`.

## Existing Codebase Anchors

- FastAPI startup and router registration: `app/main.py`
- Settings: `app/core/config.py` (vars documented in [http-contract.md](http-contract.md); see also `.env.example`)
- Auth and admin RBAC: `app/api/deps.py`
- Admin document upload (includes LightRAG forwarding when enabled): `app/api/routes/admin.py`
- User document reads: `app/api/routes/documents.py`
- Query routes: `app/api/routes/query.py`
- Read-only graph proxy routes: `app/api/routes/lightrag.py`
- Retrieval orchestration: `app/services/retrieval_service.py`
- Local vs remote routing: `app/retrieval/routing_policy.py`
- Retrieval strategies: `app/retrieval/strategies.py` (`LocalRetrievalStrategy`, `LightRAGRetrievalStrategy`)
- Local semantic/navigation/hybrid merge: `app/retrieval/router.py` and engines under `app/retrieval/*_engine.py` (excluding `lightrag_remote_engine.py`)
- Remote LightRAG engine: `app/retrieval/lightrag_remote_engine.py` (`LightRAGRemoteRetrievalEngine`)
- Remote LightRAG HTTP adapter: `app/integrations/lightrag_remote_adapter.py` (`LightRAGRemoteAdapter`)
- Local semantic embedding adapter (not HTTP): `app/integrations/lightrag_adapter.py` (`LightRAGAdapter`)
- LightRAG domain resolver: `app/integrations/lightrag_domains.py`
- Document/job/log tables: `app/storage/tables.py`
- Document repository: `app/storage/repositories/documents.py`
- Query/audit logging: `app/storage/repositories/logs.py`
- CLI graph client: `cli/services/lightrag.py`; TUI wiring: `cli/tui/state.py`, `cli/tui/screens/content.py`, `cli/tui/screens/main_menu.py`

## Ownership Boundary

`context_engine` owns:

- users and authentication
- admin permission checks
- document mirror records
- public query routes
- answer and evidence response shapes
- audit/query logs
- job/status records exposed by the app
- graph proxy routes

External LightRAG owns:

- document ingestion internals
- vector and graph indexes
- graph storage
- raw LightRAG retrieval behavior
- LightRAG deployment/runtime dependencies

## Component Decisions

### Implemented

- `LightRAGRemoteAdapter` as the HTTP adapter in `app/integrations/lightrag_remote_adapter.py`.
- `LightRAGRemoteRetrievalEngine` in `app/retrieval/lightrag_remote_engine.py`, selected by `RetrievalRoutingPolicy` when LightRAG is enabled.
- Domain manifest reader in `app/integrations/lightrag_domains.py`.
- Contract files under `external/lightrag/contract/` (`openapi.yaml` and JSON examples).
- Mocked tests with no live LightRAG dependency (`tests/test_lightrag_remote_adapter.py`, LightRAG sections in `tests/test_api.py`).
- Remote retrieval for `auto`, `semantic`, and `hybrid` when `LIGHTRAG_ENABLED=true` (upstream mode `mix`; see routing note below).
- Local **navigation** (`RetrievalMode.NAVIGATION`) stays on the local backend even when LightRAG is enabled.
- Admin upload forwarding with local mirror metadata.
- Read-only graph proxy routes in `app/api/routes/lightrag.py`.

### Routing semantics (local hybrid vs remote)

When `LIGHTRAG_ENABLED=true`, `RetrievalRoutingPolicy` sends **`auto`**, **`semantic`**, and **`hybrid`** to `LightRAGRetrievalStrategy`, which performs a **single** remote retrieve; `LightRAGRemoteAdapter` maps those modes to LightRAG **`mix`**. Local `RetrievalRouter` behaviors—query classification for `auto` and the semantic+navigation **merge** for `hybrid`—run only when the policy selects the **local** backend (`LIGHTRAG_ENABLED=false`, or any mode that does not use the remote path, e.g. `navigation` while LightRAG is on).

### Fit To Existing Code

- Preserve existing app routes such as `/query/retrieve`, `/query/answer`, and `/admin/documents/upload`.
- Route semantic/hybrid/auto retrieval through remote LightRAG when `LIGHTRAG_ENABLED=true`.
- Keep the current local retrieval path available when `LIGHTRAG_ENABLED=false`.
- Extend the existing document mirror model instead of creating a parallel registry.
- Graph proxy routes are mounted as `/graphs` and `/graph/label/...`, with no `/lightrag` prefix.

### Defer

- JSONB retrieval profiles.
- Graph editing.
- PageIndex expansion.
- Local semantic indexing replacement beyond the feature-flagged fallback.
- Any Alembic migration system unless separately approved.
- In-repo LightRAG deployment scripts or wrappers.

## Implemented Sequence

These steps are **done** in the current tree:

1. Normalized contract files under `external/lightrag/contract/`.
2. LightRAG settings mirrored in `.env.example` (`LIGHTRAG_*`).
3. Read-only domain manifest resolution (`lightrag_domains.py`).
4. `LightRAGRemoteAdapter` with typed errors and HTTP mapping.
5. Remote retrieval path behind `LIGHTRAG_ENABLED` (`RetrievalService`, strategies, `LightRAGRemoteRetrievalEngine`).
6. Admin upload creates a local mirror and forwards to LightRAG when enabled.
7. Read-only graph proxy routes (`app/api/routes/lightrag.py`).
8. Mocked tests at the adapter and API layers.

There is no in-repo LightRAG deployment wrapper script. LightRAG deployment remains external unless future backend admin deployment APIs are designed and implemented.

## Rollback Strategy

All remote behavior should be controlled by `LIGHTRAG_ENABLED`.

If external LightRAG is unavailable or the rollout needs to be paused:

- set `LIGHTRAG_ENABLED=false`
- keep existing local upload/index/retrieval behavior active
- leave contract files and external deployment assets inert
- do not remove local semantic/navigation code in v1

## Files To Avoid

Avoid editing these unless explicitly required:

- `external/lightrag/**` vendored upstream (including `lightrag.py` and `external/lightrag/api/`)
- `.references/`
- PageIndex implementation files

When **Context Engine** graph or upload response shapes change, update `cli/services/lightrag.py` (and any TUI screens that consume those payloads) alongside the API—not the vendored LightRAG tree.
