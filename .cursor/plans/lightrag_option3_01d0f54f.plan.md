---
name: LightRAG Option3
overview: "Integrate the LightRAG-only semantic retrieval refactor with Option 3 shared PostgreSQL infrastructure, capturing resolved design decisions before implementation. Then build via TDD in vertical slices: domain provisioning, LightRAG-only upload/retrieval, async ingestion/status, navigation separation, and semantic chunk removal."
todos:
  - id: docs-resolved-decisions
    content: Write the resolved Option 3 decision documentation and ADR/glossary updates.
    status: completed
  - id: tdd-domain-provisioning
    content: Add tests and implementation for per-domain PostgreSQL provisioning metadata/env rendering.
    status: completed
  - id: tdd-compose-build
    content: Add tests and implementation for local LightRAG build context and shared Docker network rendering.
    status: completed
  - id: tdd-upload-ingestion
    content: Refactor upload to `semantic_engine="lightrag"`, enqueue ingestion, and store LightRAG metadata.
    status: completed
  - id: tdd-jobs-status-locks
    content: Implement LightRAG ingestion/status polling jobs and per-domain Redis locking.
    status: completed
  - id: tdd-navigation-separation
    content: Split navigation processing from semantic readiness and use `metadata.navigation`.
    status: completed
  - id: tdd-retrieval-only-lightrag
    content: Make semantic retrieval LightRAG-only while preserving local navigation and hybrid mode.
    status: completed
  - id: tdd-remove-semantic-chunks
    content: Remove local semantic runtime code and drop `semantic_chunks` only after tests prove it is unused.
    status: completed
isProject: false
---

# LightRAG Option 3 Integration Plan

## Resolved Architecture
- Treat Option 3 as shared infrastructure, not shared ownership: Context Engine uses the same physical PostgreSQL service, but LightRAG owns its own per-domain databases and all chunks, embeddings, vector indexes, and graph data.
- Configure LightRAG persistent storage entirely in PostgreSQL: `PGKVStorage`, `PGDocStatusStorage`, `PGGraphStorage`, and `PGVectorStorage`. Redis remains for Context Engine jobs, locks, cache, and coordination.
- Use one PostgreSQL database per LightRAG domain, for example `lightrag_manuals`, plus `WORKSPACE=manuals` in the generated domain env.
- Context Engine domain manager provisions per-domain databases and limited credentials using an admin DSN from root `.env`; generated runtime credentials live only in each domain `domain.env`; `domains.json` stays non-secret.
- Put root services and generated LightRAG domain services on a shared named Docker network. LightRAG containers connect to `POSTGRES_HOST=postgres` and `POSTGRES_PORT=5432`.
- Build LightRAG from `external/lightrag` using a Context Engine-owned Dockerfile. Record/verify the LightRAG version currently present as `1.4.16`.
- Replace the current Postgres image with a validated image/build that supports both `vector` and Apache `AGE`, because `external/lightrag/kg/postgres_impl.py` uses both for `PGVectorStorage` and `PGGraphStorage`.

## Documentation To Create Or Update
- Update [`docs/brainstorm/lightrag_integration_plan_v3/refactor_doc_manager_control_plane_semantic_retrieval/00_IMPLEMENTATION_PLAN.md`](docs/brainstorm/lightrag_integration_plan_v3/refactor_doc_manager_control_plane_semantic_retrieval/00_IMPLEMENTATION_PLAN.md) with the resolved Option 3 architecture.
- Update [`docs/brainstorm/lightrag_integration_plan_v3/refactor_doc_manager_control_plane_semantic_retrieval/02_MIGRATION_AND_TEST_CHECKLIST.md`](docs/brainstorm/lightrag_integration_plan_v3/refactor_doc_manager_control_plane_semantic_retrieval/02_MIGRATION_AND_TEST_CHECKLIST.md) with Option 3-specific database, Docker, and TDD checks.
- Add a concise resolved-decisions doc under [`docs/brainstorm/lightrag_integration_plan_v3/refactor_doc_manager_control_plane_semantic_retrieval/`](docs/brainstorm/lightrag_integration_plan_v3/refactor_doc_manager_control_plane_semantic_retrieval/) so the implementation agent has one canonical handoff.
- Add a root [`CONTEXT.md`](CONTEXT.md) glossary if none exists, capturing domain terms like `LightRAG domain`, `semantic engine`, `navigation`, and `control plane` without implementation details.
- Add an ADR under [`docs/adr/`](docs/adr/) for the hard-to-reverse decision: LightRAG-only semantic retrieval with shared PostgreSQL infrastructure and per-domain LightRAG-owned databases.

## TDD Build Sequence
- Start with behavior tests around the public upload/query/domain interfaces. Use remote-adapter injection or test-only fakes; do not require a live LightRAG service for normal tests and do not reintroduce local semantic fallback.
- Slice 1: domain provisioning creates a per-domain DB name/credential plan, writes non-secret manifest metadata, and renders a domain env with `WORKSPACE`, PG storage backends, and PostgreSQL connection fields.
- Slice 2: generated compose supports local LightRAG image builds from `external/lightrag` and shared Docker networking.
- Slice 3: upload API uses `semantic_engine="lightrag"`, `lightrag_domain_id`, and separate navigation options. Non-LightRAG semantic engines return a clear 400.
- Slice 4: upload creates a local document row and enqueues `lightrag_ingest_document`; the worker uploads to LightRAG, polls status to `ready` or `failed`, and serializes same-domain ingestion with a Redis lock.
- Slice 5: navigation processing becomes a separate `navigation_process_document` job that writes parsed pages/navigation indexes and updates `documents.metadata.navigation`; it never controls semantic readiness.
- Slice 6: retrieval routing changes so `semantic` always calls LightRAG, `navigation` stays local page/tree retrieval, and `hybrid` combines LightRAG with local navigation evidence without reading `semantic_chunks`.
- Slice 7: remove runtime references to `SemanticIndexBuilder`, local fake `LightRAGAdapter`, `SemanticRetrievalEngine`, and semantic chunk repository methods.
- Slice 8: after tests prove no runtime dependency remains, add the destructive migration to drop `semantic_chunks`.

## Acceptance Focus
- Context Engine PostgreSQL stores document/control metadata only, not LightRAG embeddings or graph internals.
- LightRAG domain data is isolated by database and workspace.
- `documents.status` remains the query-facing semantic readiness state; detailed status lives under `documents.metadata.lightrag` and `documents.metadata.navigation`.
- LightRAG auth uses `X-API-Key`, matching `external/lightrag`.
- Same-domain uploads are accepted and serialized in workers.
- Existing ready documents remain queryable while a new document indexes.
- All tests are written one behavior at a time before each implementation slice.