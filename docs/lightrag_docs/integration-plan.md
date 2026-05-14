# Lean LightRAG Integration Plan

## Objective

`context_engine` uses an external LightRAG service for optional:

- admin-only document ingestion forwarding
- semantic/context retrieval
- graph visualization data

The implementation stays HTTP-only. Do not copy LightRAG internals into `app/`.

## Existing Codebase Anchors

- FastAPI startup: `app/main.py`
- Settings: `app/core/config.py`
- Auth and admin RBAC: `app/api/deps.py`
- Admin document upload: `app/api/routes/admin.py`
- User document reads: `app/api/routes/documents.py`
- Query routes: `app/api/routes/query.py`
- Retrieval orchestration: `app/services/retrieval_service.py`
- Retrieval router and engines: `app/retrieval/`
- Remote LightRAG HTTP adapter: `app/integrations/lightrag_remote_adapter.py`
- LightRAG domain resolver: `app/integrations/lightrag_domains.py`
- Document/job/log tables: `app/storage/tables.py`
- Document repository: `app/storage/repositories/documents.py`
- Query/audit logging: `app/storage/repositories/logs.py`

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
- Domain manifest reader in `app/integrations/lightrag_domains.py`.
- Contract files under `external/lightrag/contract/`.
- Mocked tests with no live LightRAG dependency.
- Remote retrieval for `auto`, `semantic`, and `hybrid` when `LIGHTRAG_ENABLED=true`.
- Local navigation retrieval even when LightRAG is enabled.
- Admin upload forwarding with local mirror metadata.
- Read-only graph proxy routes.

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

1. Add normalized contract files under `external/lightrag/contract/`.
2. Add LightRAG settings and `.env.example` entries.
3. Add read-only domain manifest resolution.
4. Add `LightRAGRemoteAdapter` with typed error handling.
5. Add a remote semantic retrieval path behind `LIGHTRAG_ENABLED`.
6. Adapt admin upload to create a local mirror record and forward to LightRAG.
7. Add read-only graph proxy routes.
8. Add mocked integration-style tests.

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

- `external/lightrag/lightrag.py`
- most files under `external/lightrag/api/`
- `.references/`
- PageIndex files
- CLI files, unless API response changes require route contract updates
