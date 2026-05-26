# Implementation Status

This file records what the current codebase implements. For the intended build sequence and maintenance roadmap, see `docs/implementation-plan.md`. For the completed mandatory-LightRAG cleanup rollout and suggested commit split, see `docs/lightrag-mandatory-cleanup-rollout.md`.

## Implemented

- FastAPI app factory, route registration, health endpoints, and Alembic-managed schema migrations.
- SQLAlchemy storage models and repositories for users, documents, jobs, rich document-processing data (pages, sections, blocks, source chunks, assets), audit logs, and query logs.
- JWT auth, password hashing, `/auth/login`, `/auth/me`, `get_current_user`, and `require_admin`.
- Admin document upload, delete, list, canonical reingest, and status refresh endpoints.
- Authenticated document list, detail, rich structure, rich page, section, chunk, and asset endpoints.
- Text, Markdown, and PDF parsing into canonical `DocumentStructure`.
- LightRAG-only semantic retrieval; local semantic chunks and deterministic embedding fallback have been removed from runtime code.
- Retrieval with `semantic`, `navigation`, `hybrid`, and `auto` modes; `RetrievalRoutingPolicy` selects local navigation versus LightRAG-backed retrieval; `LightRAGRetrievalStrategy` combines LightRAG evidence with rich local navigation evidence for hybrid mode.
- Evidence-only retrieval via `POST /retrieve`.
- Admin-only debug details when `include_debug=true`.
- Job table, job status endpoints, Redis `rq` enqueue path, and worker-owned job lifecycle.
- Audit/query log repositories and admin log endpoints.
- Seed admin, backup, and retrieval evaluation scripts.
- Legacy terminal UI/CLI code remains in-repo but is deprecated and unsupported for active workflows.
- Remote LightRAG integration for semantic retrieval/runtime, including HTTP adapter, domain manifest resolution, retrieval strategy, queued ingestion jobs, status refresh, and graph proxy routes.
- LightRAG domain deployment control behind `LIGHTRAG_DEPLOY_ENABLED`, including managed domain manifest, generated domain env files, generated compose file, fakeable Docker Compose runner, admin APIs in `app/api/routes/lightrag_admin.py`, user-safe `GET /lightrag/domains`, domain-aware upload/query selection, and per-domain PostgreSQL storage metadata.
- LightRAG provider configuration contract for generated `domain.env` files, including `LLM_BINDING*`, `EMBEDDING_BINDING*`, and `OPENAI_LLM_*` tuning fields sourced from root `LIGHTRAG_*` settings.
- Bedrock OpenAI-compatible support path by keeping LightRAG bindings as `openai` and setting `LIGHTRAG_LLM_BINDING_HOST` to `https://bedrock-runtime.<region>.amazonaws.com/openai/v1`.
- Provider secret boundary enforcement: provider API keys are emitted only to per-domain `domain.env` files and are not written into compose output, manifest JSON, or admin/user domain API responses.
- Contract files under `external/lightrag/contract/`.
- Behavior tests for API, routing policy, LightRAG adapter, LightRAG deploy stack, auth guardrails, upload, retrieval flow, queued jobs, and worker failure handling. Legacy CLI/TUI tests remain while deprecation cleanup is pending.
- Canonical document-processing scaffolding for `DocumentStructure`, pages, sections, blocks, source chunks, assets, structure quality, storage paths, and document-processing repository persistence.
- The LightRAG ingestion job now uses the existing upload/job flow to build and persist canonical `DocumentStructure` plus `SourceChunk` rows for parseable text/Markdown uploads, and it can use the real `DoclingParser` boundary for PDFs when Docling is installed. Built Source Chunks include section title/path metadata and section-prefixed chunk text that is forwarded to LightRAG alongside document, section, block, page, and asset IDs. Structure-processing failures fail ingestion explicitly (no raw LightRAG upload fallback).
- Document asset extraction saves assets, generates resized thumbnails when Pillow can read the asset, computes content hashes, extracts figure/image/table snapshots when Docling exposes image data, and deduplicates identical asset payloads while preserving per-occurrence metadata links.
- The Docling parser normalizes label variants (for example `section-header`), uses provenance fallback when primary page numbers are missing, and carries detached caption blocks into subsequent image/table assets when item-level caption APIs are empty.
- Deterministic structure quality scoring is retained; runtime TOC refinement and TOC refinement report APIs are removed from ingestion and HTTP routes.
- Authenticated document debug APIs expose canonical structure data: `GET /documents/{document_id}/structure`, `GET /documents/{document_id}/structure-quality`, `GET /documents/{document_id}/sections/{section_id}`, `GET /documents/{document_id}/chunks/{chunk_id}`, and authenticated asset/thumbnail streaming.
- Retrieval asset enrichment can resolve assets from LightRAG evidence using legacy `metadata.source_chunk_id`, chunk-ingest `metadata.chunk_id`, or returned `metadata.asset_ids`, then rank and limit assets using direct chunk links, block links, caption/query overlap, page proximity, and section proximity.
- Legacy CLI service wrappers and TUI/screen renderers remain in-repo but are deprecated and unsupported.
- Single rich navigation is implemented end-to-end: local navigation retrieval uses `RichNavigationEngine` over canonical `DocumentStructure`, and legacy `parsed_documents`/`navigation_indexes` runtime paths have been removed.
- Canonical ingestion job kind is `document_ingest`; legacy runtime aliases have been removed after the Alembic data migration.

## LightRAG Runtime Behavior

Remote LightRAG is the required integration runtime. Tests may inject/fake the remote adapter boundary, but runtime semantic retrieval has no local fallback.

Runtime behavior:

- `auto`, `semantic`, and `hybrid` semantic retrieval use `LightRAGRemoteRetrievalEngine` and `LightRAGRemoteAdapter`; `hybrid` can add local rich-navigation evidence.
- `navigation` retrieval remains local and is powered by `RichNavigationEngine`.
- Admin upload stores a local mirror record/file and enqueues `document_ingest`.
- Uploads require a LightRAG domain manifest so requested domains are explicit and validated.
- Upload responses include the LightRAG ingestion job id; LightRAG status is tracked under `documents.metadata.lightrag`.
- Domain-scoped graph routes under `GET /lightrag/domains/{domain_id}/graphs` and `GET /lightrag/domains/{domain_id}/graph/labels...` proxy to the remote LightRAG service.
- LightRAG timeouts/connect failures become `503`; auth/upstream/invalid-response failures become `502`.

## Intentional Simplifications

- Alembic is the production schema source of truth; local test helpers may still create tables directly for isolated tests.
- Context Engine stores LightRAG metadata and canonical local navigation structure; LightRAG owns semantic chunks, embeddings, vector indexes, and graph data.
- Current text/Markdown ingestion still uses `TextDoclingParser`, a lightweight stub. The `DoclingParser` boundary and asset extraction exist with focused fake Docling fixtures, but broader real-PDF fixture coverage remains pending.
- Runtime TOC refinement has been removed from ingestion. Structure quality scoring remains available via deterministic local logic.
- Source Chunk ingestion is production-wired through `StructureAwareChunkBuilder`, including section-aware grouping, page ranges, inherited assets, section title/path metadata, section-prefixed chunk text, and caption text for asset-only chunks. Better sizing/tuning against real Docling output remains pending.
- The retrieval API is evidence-only and does not compose natural-language answers in backend responses.
- Document ACLs are deferred; authenticated users can read ready documents.
- LightRAG domain deployment control is opt-in and generates a separate `.data/lightrag/docker-compose.lightrag-domains.yml`; generated domain services share the root Docker network.
- Registry entry `api_key` values and `LIGHTRAG_LLM_BINDING_API_KEY` have distinct responsibilities: the former authenticates Context Engine -> a registered LightRAG server, while the latter authenticates LightRAG -> model provider traffic.

## Next Hardening Items

- Add rate limiting middleware and stronger request-size controls.
- Expand evaluation datasets and retrieval metrics.
- Add richer LightRAG status polling and database provisioning operations.
- Harden real-PDF Docling fixtures (table/figure/caption variation coverage) and tune parser normalization against real outputs.
- Tune `StructureAwareChunkBuilder` sizing and text-shaping against real Docling outputs.

