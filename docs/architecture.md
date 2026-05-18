# Backend Architecture

The app is a backend-only multi-user Context Engine. It exposes one FastAPI API, one auth model, one document registry, one job system, one optional LightRAG deployment control plane, and a common `Evidence` contract across local retrieval and optional remote LightRAG retrieval.

## System Shape

```text
HTTP client or `context-engine` TUI (`context-engine` / `context-tui`)
  -> FastAPI route
  -> application service
  -> repository / retrieval router / job queue / remote adapter
  -> storage or retrieval engine
  -> response schema
```

Retrieval has two runtime backends. `RetrievalRoutingPolicy` in `app/retrieval/routing_policy.py` picks `RetrievalBackend.LOCAL` versus `RetrievalBackend.LIGHTRAG`; `RetrievalService` dispatches through small strategy objects in `app/retrieval/strategies.py` (`LocalRetrievalStrategy` wraps `RetrievalRouter`; `LightRAGRetrievalStrategy` wraps `LightRAGRemoteRetrievalEngine`). That keeps one routing matrix in code and docs:

```text
LIGHTRAG_ENABLED=false
  RetrievalService
    -> LocalRetrievalStrategy
    -> RetrievalRouter
       -> SemanticRetrievalEngine
       -> NavigationRetrievalEngine
       -> HybridMerger

LIGHTRAG_ENABLED=true and mode in auto|semantic|hybrid
  RetrievalService
    -> LightRAGRetrievalStrategy
    -> LightRAGRemoteRetrievalEngine
       -> LightRAGRemoteAdapter
       -> external LightRAG HTTP API

LIGHTRAG_ENABLED=true and mode=navigation
  RetrievalService
    -> LocalRetrievalStrategy
    -> RetrievalRouter navigation path
```

Both paths return local `Evidence` objects. API routes never expose raw LightRAG, PageIndex, or storage rows.

## Package Ownership

- `app/api/`: HTTP routes and dependency wiring only. LightRAG graph proxies live in `app/api/routes/lightrag.py`; admin domain lifecycle and the user-safe domain list live in `app/api/routes/lightrag_admin.py` alongside other admin routers in `app/api/routes/admin.py`.
- `app/core/`: configuration, logging, security, and error helpers.
- `app/domain/`: dataclasses/enums that define the app vocabulary.
- `app/schemas/`: Pydantic request/response models.
- `app/services/`: use cases and orchestration.
- `app/retrieval/`: retrieval interfaces, local engines, router, merger, and answer composition.
- `app/indexing/`: parsers, chunking, navigation index builder, and semantic index builder.
- `app/integrations/`: wrappers around external/reference systems, including remote LightRAG HTTP.
- `app/lightrag_deploy/`: admin-only LightRAG domain deployment control, manifest/env/compose generation, and Docker Compose runner boundary.
- `app/storage/`: database session and repositories.
- `app/workers/`: Redis queue and background indexing tasks.
- `cli/`: TUI launcher (`cli/launcher.py`), argparse-backed settings (`cli/config.py`), credential storage (`cli/credentials.py`), `ApiClient` (`cli/api_client.py`), typed HTTP helpers (`cli/services/`), optional query JSON builders (`cli/query_payload.py`). The interactive UI is Rich-based under `cli/tui/` (`app.py`, `navigation.py`, `screen.py`, `session_flow.py`, `state.py`, `styles.py`, `keys.py`, TUI-local `screens/` and `renderers/`). ASCII screen layouts and reusable tables live under `cli/screens/` and `cli/renderers/`; guided multi-step UX helpers live under `cli/flows/` and are composed into TUI stacks rather than exposing separate Typer commands. Legacy `cli/main.py` delegates to the launcher (`app()` callable for backwards-compatible imports).
- `scripts/`: seed, backup, and evaluation commands.
- `tests/`: behavior tests through API, terminal client helpers, adapter, or public service interfaces.

## Request Flow: Query

```text
POST /query, /query/retrieve, or /query/answer
  -> QueryRequest (optional document filter, optional lightrag_domain_id)
  -> auth dependency
  -> RetrievalService (routing policy + local/remote strategy)
  -> local RetrievalRouter or remote LightRAG adapter
  -> EvidenceResponse list
  -> optional AnswerComposer
  -> response schema
```

`mode=auto` uses deterministic local routing when LightRAG is disabled. When LightRAG is enabled, `auto`, `semantic`, and `hybrid` are sent to LightRAG as `mix`; `navigation` stays local.

`include_debug` is accepted on query requests, but debug details are returned only for admin users.

## Request Flow: Upload and Index

```text
LIGHTRAG_ENABLED=false
  POST /admin/documents/upload
    -> require_admin
    -> DocumentService stores file and metadata
    -> JobService enqueues or runs indexing
    -> response includes document_id and job_id

worker
  -> parse document
  -> build navigation index
  -> build semantic index
  -> mark active index version ready
```

```text
LIGHTRAG_ENABLED=true
  POST /admin/documents/upload
    -> require_admin
    -> DocumentService stores a local mirror record and file
    -> LightRAGRemoteAdapter forwards multipart upload
    -> response includes document_id, job_id null, and lightrag metadata
```

Local indexing uses the worker/job system. Remote LightRAG ingestion is owned by the external LightRAG service and tracked through mirrored metadata such as `lightrag.track_id`.

## LightRAG Domain Deployment Control

Runtime LightRAG traffic remains HTTP-only through `LightRAGRemoteAdapter`. Deployment control is separate:

```text
Admin API or TUI
  -> LightRAGDomainService
  -> .data/lightrag/domains.json + generated domain.env files
  -> generated .data/lightrag/docker-compose.lightrag-domains.yml
  -> Docker Compose runner
```

Deployment routes are disabled by default with `LIGHTRAG_DEPLOY_ENABLED=false`. When enabled, admins can create, list, show, regenerate, start, stop, recreate, archive, or explicitly permanently delete domains. Any authenticated user may call `GET /lightrag/domains` for a safe subset of domain metadata used to pick `lightrag_domain_id` on uploads and queries (admin mutating routes still require deploy mode on).

Each managed domain lives under `.data/lightrag/domains/<domain>/` and gets one generated `domain.env`. Domain removal archives data by default under `.data/lightrag/deleted/`.

## LightRAG Graph Proxy

The API exposes authenticated read-only graph proxy routes:

- `GET /graphs`
- `GET /graph/label/list`
- `GET /graph/label/popular`
- `GET /graph/label/search`

These routes call the configured remote LightRAG service only when `LIGHTRAG_ENABLED=true`. When disabled, they return HTTP `400` with a disabled LightRAG message instead of falling back locally.

## Storage

Local development defaults are deliberately small:

- SQLite database at `.data/context_engine.db` unless `DATABASE_URL` overrides it.
- Local filesystem uploads under `.data/uploads` unless `STORAGE_ROOT` overrides it.
- Redis URL defaults to `redis://localhost:6379/0`, with background jobs used when `INDEX_JOBS_INLINE=false`.
- Semantic chunks currently use deterministic local embeddings stored in normal database fields, which keeps tests and local development credential-free.

Docker Compose uses PostgreSQL with the `pgvector/pgvector` image, Redis, API, and worker services. Real pgvector column/type usage remains a hardening item; do not assume every local run uses pgvector.

## Security

All routes require authentication except health and login. Admin-only operations use a single `require_admin` dependency.

V1 document read policy: every authenticated user may read/query ready, non-deleted documents. Document-level ACLs are deferred.

## Evidence Contract

Every retrieval engine returns:

- `id`
- `document_id`
- `source_engine`
- `text`
- optional `score`
- optional page range
- optional section reference
- metadata

The internal domain model names the evidence identifier `id`. Public query responses expose the same value as `evidence_id` so clients do not confuse evidence IDs with document IDs. The answer composer consumes domain `Evidence` directly and cites evidence IDs, not raw database rows.

## Hybrid Merge Rules

Local hybrid retrieval queries both local engines, then:

1. Deduplicates by document, page range, and normalized text hash.
2. Normalizes missing scores to `0.5`.
3. Prefers page/section evidence when scores are close.
4. Keeps at most `top_k` items.
5. Preserves source engine metadata.

When LightRAG handles `hybrid`, upstream retrieval and ranking are owned by LightRAG and normalized back into local evidence.

## Failure Model

- Upload failure returns a request error and creates no usable document record.
- Local index failure marks the job failed and leaves the previous active index untouched.
- LightRAG timeout/connect failures become service-unavailable responses.
- LightRAG auth/upstream/invalid-response failures become bad-gateway style responses.
- Query failure returns a structured API error.
- Weak evidence produces a refusal unless the request explicitly allows fallback. In the deterministic composer, evidence is weak only when every evidence item has a numeric score below `0.2`; unscored evidence is not treated as weak.

