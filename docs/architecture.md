# Backend Architecture

The app is a backend-only multi-user Context Engine. It exposes one FastAPI API, one auth model, one document registry, one job system, one LightRAG deployment control plane, and a common `Evidence` contract across LightRAG semantic retrieval and local document navigation.

## System Shape

```text
HTTP client or `context-engine` TUI
  -> FastAPI route
  -> application service
  -> repository / retrieval strategy / job queue / remote adapter
  -> storage or retrieval engine
  -> response schema
```

Retrieval has two runtime capabilities: mandatory remote LightRAG semantic retrieval and local rich navigation retrieval from canonical `DocumentStructure`. `RetrievalRoutingPolicy` in `app/retrieval/routing_policy.py` selects the backend by retrieval mode, and `RetrievalService` dispatches through strategy objects in `app/retrieval/strategies.py`.

```text
mode=navigation
  RetrievalService
    -> LocalRetrievalStrategy
    -> RichNavigationEngine

mode in auto|semantic|hybrid
  RetrievalService
    -> LightRAGRetrievalStrategy
    -> LightRAGRemoteRetrievalEngine
       -> LightRAGRemoteAdapter
       -> external LightRAG HTTP API
    -> RichNavigationEngine for hybrid enrichment
```

Both paths return local `Evidence` objects. API routes never expose raw LightRAG, PageIndex, or storage rows.

## Processing Status Flow

Processing status is served from Context Engine as a normalized contract; clients do not call LightRAG status endpoints directly.

```text
client
  -> /lightrag/domains/{domain_id}/processing-status (user)
     or /admin/lightrag/domains/{domain_id}/processing-status (admin)
  -> ProcessingStatusService
  -> DocumentRepository + JobRepository (local truth)
  -> LightRAGRemoteAdapter.pipeline_status/status_counts (remote enrichment)
  -> ProcessingStatusCache TTL coalescing
  -> normalized state/counts/active response
```

Document-level status follows the same pattern through:

- `GET /documents/{document_id}/processing-status`
- `GET /admin/documents/{document_id}/processing-status`

## Package Ownership

- `app/api/`: HTTP routes and dependency wiring only. LightRAG graph proxies live in `app/api/routes/lightrag.py`; admin domain lifecycle and the user-safe domain list live in `app/api/routes/lightrag_admin.py` alongside other admin routers in `app/api/routes/admin.py`.
- `app/core/`: configuration, logging, security, and error helpers.
- `app/domain/`: dataclasses/enums that define the app vocabulary.
- `app/schemas/`: Pydantic request/response models.
- `app/services/`: use cases and orchestration.
- `app/retrieval/`: retrieval interfaces, rich navigation engine, LightRAG remote engine, routing policy, strategies, and merger.
- `app/integrations/`: wrappers around external/reference systems, including remote LightRAG HTTP.
- `app/lightrag_deploy/`: admin-only LightRAG domain deployment control, manifest/env/compose generation, and Docker Compose runner boundary.
- `app/storage/`: database session and repositories.
- `app/workers/`: Redis queue and background indexing tasks.
- `cli/`: TUI launcher (`cli/launcher.py`), argparse-backed settings (`cli/config.py`), credential storage (`cli/credentials.py`), `ApiClient` (`cli/api_client.py`), typed HTTP helpers (`cli/services/`), and retrieve JSON builders (`cli/retrieve_payload.py`). The interactive UI is Rich-based under `cli/tui/` (`app.py`, `navigation.py`, `screen.py`, `session_flow.py`, `state.py`, `styles.py`, `keys.py`, TUI-local `screens/` and `renderers/`). ASCII screen layouts and reusable tables live under `cli/screens/` and `cli/renderers/`; guided multi-step UX helpers live under `cli/flows/` and are composed into TUI stacks rather than exposing separate Typer commands. Legacy `cli/main.py` delegates to the launcher (`app()` callable for backwards-compatible imports).
- `scripts/`: seed, backup, and evaluation commands.
- `tests/`: behavior tests through API, terminal client helpers, adapter, or public service interfaces.

## Request Flow: Retrieve

```text
POST /retrieve
  -> RetrieveRequest (optional document filter, optional lightrag_domain_id)
  -> auth dependency
  -> RetrievalService (routing policy + local/remote strategy)
  -> RichNavigationEngine or LightRAGRemoteAdapter
  -> EvidenceResponse list
  -> RetrieveResponse
```

`auto`, `semantic`, and `hybrid` are sent to LightRAG as `mix`; `hybrid` may add local rich-navigation evidence. `navigation` stays local deterministic retrieval over pages/sections/blocks/chunks/assets. There is no semantic fallback to local navigation when LightRAG fails.

`include_debug` is accepted on retrieve requests, but debug details are returned only for admin users.

## Request Flow: Upload and Index

```text
LightRAG runtime configured
  POST /admin/documents/upload
    -> require_admin
    -> DocumentService stores a local mirror record and file
    -> JobService enqueues document_ingest
    -> validate LightRAG domain manifest and requested domain
    -> response includes document_id, lightrag job_id, and queued lightrag metadata
```

Admin uploads require a readable LightRAG domain manifest. Structure-aware ingestion must produce source chunks before LightRAG ingest proceeds; parse/build failures mark the document failed instead of raw-uploading to LightRAG.

Remote LightRAG ingestion is started by a worker job, serialized per domain with a Redis lock, and tracked through mirrored metadata such as `lightrag.track_id`.

When Docling is available for PDF parsing, ingestion normalizes label variants (for example `section-header`), falls back across provenance entries for page-number resolution, and maps detached caption blocks to nearby image/table assets when per-item caption APIs are empty.

## LightRAG Domain Deployment Control

Runtime LightRAG traffic remains HTTP-only through `LightRAGRemoteAdapter`. Deployment control is separate:

```text
Admin API or TUI
  -> LightRAGDomainService
  -> .data/lightrag/domains.json + generated domain.env files
  -> generated .data/lightrag/docker-compose.lightrag-domains.yml
  -> Docker Compose runner
```

Admins can create, list, show, start, stop, repair, archive, preview purge, and purge domains through `/admin/lightrag/domains...`. Advanced compatibility routes (`recreate`, `regenerate`) still exist but are not part of the normal admin lifecycle UX. Any authenticated user may call `GET /lightrag/domains` for a safe subset of domain metadata used to pick `lightrag_domain_id` on uploads and queries.

Each managed domain lives under `.data/lightrag/domains/<domain>/`, gets one generated `domain.env`, and uses a LightRAG-owned PostgreSQL database such as `lightrag_manuals`. Domain removal archives data by default under `.data/lightrag/deleted/`. Permanent deletion is handled through explicit `purge-preview` plus `purge`; `DELETE ...?permanent=true` is deprecated and rejected.

The generated `domain.env` now includes provider runtime wiring (when configured) for:

- `LLM_BINDING`, `LLM_BINDING_HOST`, `LLM_BINDING_API_KEY`, `LLM_MODEL`
- Optional `KEYWORD_LLM_MODEL`, `QUERY_LLM_MODEL`, `VLM_LLM_MODEL`
- `EMBEDDING_BINDING`, `EMBEDDING_BINDING_HOST`, `EMBEDDING_BINDING_API_KEY`, `EMBEDDING_MODEL`, `EMBEDDING_DIM`, `EMBEDDING_TOKEN_LIMIT`, `EMBEDDING_SEND_DIM`, `EMBEDDING_USE_BASE64`
- Optional `OPENAI_LLM_MAX_TOKENS`, `OPENAI_LLM_MAX_COMPLETION_TOKENS`, `OPENAI_LLM_TEMPERATURE`, `OPENAI_LLM_EXTRA_BODY`

For Bedrock OpenAI-compatible routing, the supported pattern is LightRAG `openai` binding + Bedrock OpenAI-compatible host URL (`https://bedrock-runtime.<region>.amazonaws.com/openai/v1`). This preserves LightRAG's OpenAI binding surface while targeting Bedrock.

## LightRAG Graph Proxy

The API exposes authenticated read-only graph proxy routes:

- `GET /lightrag/domains/{domain_id}/graphs`
- `GET /lightrag/domains/{domain_id}/graph/labels`
- `GET /lightrag/domains/{domain_id}/graph/labels/popular`
- `GET /lightrag/domains/{domain_id}/graph/labels/search`

These routes call the configured remote LightRAG service and do not fall back to any local semantic implementation.

## Storage

Local development uses explicit service-backed storage:

- PostgreSQL through required `DATABASE_URL`; sqlite is only allowed for explicit isolated tests.
- Local filesystem uploads under `.data/uploads` unless `STORAGE_ROOT` overrides it.
- Redis URL defaults to `redis://localhost:6379/0`, with background jobs used when `INDEX_JOBS_INLINE=false`.
- Context Engine stores LightRAG document IDs, track IDs, status, and canonical local structure metadata; it does not store semantic chunks or embeddings.

Docker Compose uses PostgreSQL, Redis, API, worker, and generated LightRAG domain services on a shared named network. Option 3 requires a validated PostgreSQL image/build with both `vector` and Apache `AGE` extensions.

When `LIGHTRAG_DOCKER_EXECUTION_MODE=socket`, the API container mounts the host Docker socket so admin domain lifecycle operations can start, stop, and repair generated LightRAG services. Treat this mode as a privileged local/operator boundary; production deployments should isolate or replace that control path rather than exposing it as an ordinary web runtime permission.

## Security

All routes require authentication except health and login. Admin-only operations use a single `require_admin` dependency.

V1 document read policy: every authenticated user may read/query ready, non-deleted documents. Document-level ACLs are deferred.

Deployment secret boundaries:

- Per-domain registry `api_key` values authenticate Context Engine -> registered LightRAG server traffic.
- Provider keys from `LIGHTRAG_LLM_BINDING_API_KEY` / `LIGHTRAG_EMBEDDING_BINDING_API_KEY` are emitted only to generated per-domain `domain.env` files.
- Domain manifest and generated compose output do not inline provider secrets; compose references `env_file` paths instead.

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

The internal domain model names the evidence identifier `id`. Public retrieval responses expose the same value as `evidence_id` so clients do not confuse evidence IDs with document IDs.

## Hybrid Merge Rules

Hybrid retrieval combines LightRAG semantic evidence with local rich-navigation evidence when local structure data exists, then:

1. Deduplicates by document, page range, and normalized text hash.
2. Normalizes missing scores to `0.5`.
3. Prefers page/section evidence when scores are close.
4. Keeps at most `top_k` items.
5. Preserves source engine metadata.

LightRAG owns semantic retrieval and ranking. Context Engine only normalizes LightRAG results into local evidence and optionally merges navigation evidence.

## Failure Model

- Upload failure returns a request error and creates no usable document record.
- LightRAG ingestion failure marks the ingestion job failed and updates the document's LightRAG status metadata.
- LightRAG timeout/connect failures become service-unavailable responses.
- LightRAG auth/upstream/invalid-response failures become bad-gateway style responses.
- Retrieve failure returns a structured API error.
- Processing status degrades to stale/partial responses when LightRAG status calls fail; local document/job truth remains available via normalized counts/state.

