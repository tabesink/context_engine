# Backend Architecture

The app is a backend-only multi-user hybrid RAG system. It exposes one FastAPI API, one auth model, one document registry, one job system, and two retrieval engines behind a common evidence contract.

## System Shape

```text
HTTP client
  -> FastAPI route
  -> application service
  -> repository / retrieval router / job queue
  -> storage or retrieval engine
  -> response schema
```

Retrieval stays split:

```text
RetrievalRouter
  -> SemanticRetrievalEngine
       -> LightRAGAdapter
       -> pgvector / semantic index
  -> NavigationRetrievalEngine
       -> PageIndexAdapter
       -> page tree / page text
```

Both engines return `Evidence`. The API never exposes raw LightRAG or PageIndex objects.

## Package Ownership

- `app/api/`: HTTP routes and dependency wiring only.
- `app/core/`: configuration, logging, security, error helpers.
- `app/domain/`: dataclasses/enums that define the app vocabulary.
- `app/schemas/`: Pydantic request/response models.
- `app/services/`: use cases and orchestration.
- `app/retrieval/`: retrieval interfaces, engines, router, merger, and answer composition.
- `app/indexing/`: parsers, chunking, navigation index builder, semantic index builder.
- `app/integrations/`: wrappers around external or reference code.
- `app/storage/`: database session and repositories.
- `app/workers/`: Redis queue and background indexing tasks.
- `scripts/`: seed, backup, restore, and evaluation commands.
- `tests/`: behavior tests through API or public service interfaces.

## Request Flow: Query

```text
POST /query
  -> QueryRequest
  -> auth dependency
  -> RetrievalService
  -> RetrievalRouter
  -> one or both engines
  -> HybridMerger
  -> AnswerComposer
  -> QueryResponse
```

`mode=auto` uses deterministic routing first. LLM routing is not a V1 dependency.

## Request Flow: Upload and Index

```text
POST /admin/documents/upload
  -> require_admin
  -> DocumentService stores file and metadata
  -> JobService enqueues indexing job
  -> response includes document_id and job_id

worker
  -> parse document
  -> build navigation index
  -> build semantic index
  -> mark active index version ready
```

The API may offer explicit index/reindex endpoints, but indexing does not run in the request lifecycle.

## Storage

V1 storage is deliberately small:

- PostgreSQL stores users, roles, document registry, jobs, audit logs, query logs, parsed document metadata, navigation trees, and index versions.
- pgvector stores semantic chunk embeddings.
- Redis stores queue state.
- Local filesystem stores original uploaded files.

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

The answer composer cites evidence IDs, not raw database rows.

## Hybrid Merge Rules

Hybrid retrieval queries both engines concurrently, then:

1. Deduplicates by document, page range, and normalized text hash.
2. Normalizes missing scores to `0.5`.
3. Prefers page/section evidence when scores are close.
4. Keeps at most `top_k` items.
5. Preserves source engine metadata.

## Failure Model

- Upload failure returns a request error and creates no document record.
- Index failure marks the job failed and leaves the previous active index untouched.
- Query failure returns a structured API error.
- Weak evidence produces a refusal unless the request explicitly allows fallback.

