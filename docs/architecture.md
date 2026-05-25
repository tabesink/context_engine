# Backend Architecture

The app is a backend-only multi-user Context Engine. It exposes one FastAPI API, one auth model, one document registry, one job system, one LightRAG deployment control plane, and a common `Evidence` contract across LightRAG semantic retrieval and local document navigation.

## System Shape

```text
HTTP client or `context-engine` TUI (`context-engine` / `context-tui`)
  -> FastAPI route
  -> application service
  -> repository / retrieval router / job queue / remote adapter
  -> storage or retrieval engine
  -> response schema
```

Retrieval has two runtime capabilities: mandatory remote LightRAG semantic retrieval and local navigation/page retrieval. `RetrievalRoutingPolicy` in `app/retrieval/routing_policy.py` selects the backend by retrieval mode, and `RetrievalService` dispatches through strategy objects in `app/retrieval/strategies.py`.

```text
mode=navigation
  RetrievalService
    -> LocalRetrievalStrategy
    -> NavigationRetrievalEngine

mode in auto|semantic|hybrid
  RetrievalService
    -> LightRAGRetrievalStrategy
    -> LightRAGRemoteRetrievalEngine
       -> LightRAGRemoteAdapter
       -> external LightRAG HTTP API
    -> NavigationRetrievalEngine for hybrid enrichment
```

Both paths return local `Evidence` objects. API routes never expose raw LightRAG, PageIndex, or storage rows.

## Package Ownership

- `app/api/`: HTTP routes and dependency wiring only. LightRAG graph proxies live in `app/api/routes/lightrag.py`; admin domain lifecycle and the user-safe domain list live in `app/api/routes/lightrag_admin.py` alongside other admin routers in `app/api/routes/admin.py`.
- `app/core/`: configuration, logging, security, and error helpers.
- `app/domain/`: dataclasses/enums that define the app vocabulary.
- `app/schemas/`: Pydantic request/response models.
- `app/services/`: use cases and orchestration.
- `app/retrieval/`: retrieval interfaces, local navigation engine, LightRAG remote engine, router, merger, and answer composition.
- `app/indexing/`: parsers, chunking helpers, and navigation index builder.
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
  -> NavigationRetrievalEngine or LightRAGRemoteAdapter
  -> EvidenceResponse list
  -> optional AnswerComposer
  -> response schema
```

`auto`, `semantic`, and `hybrid` are sent to LightRAG as `mix`; `hybrid` may add local navigation evidence. `navigation` stays local page/tree retrieval. There is no semantic fallback to local navigation when LightRAG fails.

`include_debug` is accepted on query requests, but debug details are returned only for admin users.

## Request Flow: Upload and Index

```text
LIGHTRAG_ENABLED=true (required)
  POST /admin/documents/upload
    -> require_admin
    -> DocumentService stores a local mirror record and file
    -> JobService enqueues lightrag_ingest_document
    -> optional navigation_process_document job updates metadata.navigation
    -> validate LightRAG domain manifest and requested domain
    -> response includes document_id, lightrag job_id, and queued lightrag metadata
```

Admin uploads require a readable LightRAG domain manifest. Structure-aware ingestion must produce source chunks before LightRAG ingest proceeds; parse/build failures mark the document failed instead of raw-uploading to LightRAG.

Navigation processing uses the worker/job system. Remote LightRAG ingestion is started by a worker job, serialized per domain with a Redis lock, and tracked through mirrored metadata such as `lightrag.track_id`.

When Docling is available for PDF parsing, ingestion normalizes label variants (for example `section-header`), falls back across provenance entries for page-number resolution, and maps detached caption blocks to nearby image/table assets when per-item caption APIs are empty. TOC refinement rejections now include validation details (accuracy, inferred offset, and section starts) in the persisted report warnings.

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

Each managed domain lives under `.data/lightrag/domains/<domain>/`, gets one generated `domain.env`, and uses a LightRAG-owned PostgreSQL database such as `lightrag_manuals`. Domain removal archives data by default under `.data/lightrag/deleted/`.

The generated `domain.env` now includes provider runtime wiring (when configured) for:

- `LLM_BINDING`, `LLM_BINDING_HOST`, `LLM_BINDING_API_KEY`, `LLM_MODEL`
- Optional `KEYWORD_LLM_MODEL`, `QUERY_LLM_MODEL`, `VLM_LLM_MODEL`
- `EMBEDDING_BINDING`, `EMBEDDING_BINDING_HOST`, `EMBEDDING_BINDING_API_KEY`, `EMBEDDING_MODEL`, `EMBEDDING_DIM`, `EMBEDDING_TOKEN_LIMIT`, `EMBEDDING_SEND_DIM`, `EMBEDDING_USE_BASE64`
- Optional `OPENAI_LLM_MAX_TOKENS`, `OPENAI_LLM_MAX_COMPLETION_TOKENS`, `OPENAI_LLM_TEMPERATURE`, `OPENAI_LLM_EXTRA_BODY`

For Bedrock OpenAI-compatible routing, the supported pattern is LightRAG `openai` binding + Bedrock OpenAI-compatible host URL (`https://bedrock-runtime.<region>.amazonaws.com/openai/v1`). This preserves LightRAG's OpenAI binding surface while targeting Bedrock.

## LightRAG Graph Proxy

The API exposes authenticated read-only graph proxy routes:

- `GET /graphs`
- `GET /graph/label/list`
- `GET /graph/label/popular`
- `GET /graph/label/search`

These routes call the configured remote LightRAG service and do not fall back to any local semantic implementation.

## Storage

Local development defaults are deliberately small:

- SQLite database at `.data/context_engine.db` unless `DATABASE_URL` overrides it.
- Local filesystem uploads under `.data/uploads` unless `STORAGE_ROOT` overrides it.
- Redis URL defaults to `redis://localhost:6379/0`, with background jobs used when `INDEX_JOBS_INLINE=false`.
- Context Engine stores LightRAG document IDs, track IDs, status, and navigation metadata; it does not store semantic chunks or embeddings.

Docker Compose uses PostgreSQL, Redis, API, worker, and generated LightRAG domain services on a shared named network. Option 3 requires a validated PostgreSQL image/build with both `vector` and Apache `AGE` extensions.

## Security

All routes require authentication except health and login. Admin-only operations use a single `require_admin` dependency.

V1 document read policy: every authenticated user may read/query ready, non-deleted documents. Document-level ACLs are deferred.

Deployment secret boundaries:

- `LIGHTRAG_API_KEY` (Context Engine -> LightRAG server auth) remains root app configuration and is not copied into manifests.
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

The internal domain model names the evidence identifier `id`. Public query responses expose the same value as `evidence_id` so clients do not confuse evidence IDs with document IDs. The answer composer consumes domain `Evidence` directly and cites evidence IDs, not raw database rows.

## Hybrid Merge Rules

Hybrid retrieval combines LightRAG semantic evidence with local navigation evidence when local navigation data exists, then:

1. Deduplicates by document, page range, and normalized text hash.
2. Normalizes missing scores to `0.5`.
3. Prefers page/section evidence when scores are close.
4. Keeps at most `top_k` items.
5. Preserves source engine metadata.

LightRAG owns semantic retrieval and ranking. Context Engine only normalizes LightRAG results into local evidence and optionally merges navigation evidence.

## Failure Model

- Upload failure returns a request error and creates no usable document record.
- Navigation processing failure marks the navigation job failed and records `metadata.navigation.status="failed"` without changing semantic readiness.
- LightRAG ingestion failure marks the ingestion job failed and updates the document's LightRAG status metadata.
- LightRAG timeout/connect failures become service-unavailable responses.
- LightRAG auth/upstream/invalid-response failures become bad-gateway style responses.
- Query failure returns a structured API error.
- Weak evidence produces a refusal unless the request explicitly allows fallback. In the deterministic composer, evidence is weak only when every evidence item has a numeric score below `0.2`; unscored evidence is not treated as weak.

