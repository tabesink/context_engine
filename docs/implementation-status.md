# Implementation Status

This file records what the current codebase implements. For the intended build sequence and maintenance roadmap, see `docs/implementation-plan.md`. For the completed mandatory-LightRAG cleanup rollout and suggested commit split, see `docs/lightrag-mandatory-cleanup-rollout.md`.

## Implemented

- FastAPI app factory, route registration, health endpoints, and startup table creation.
- SQLAlchemy storage models and repositories for users, documents, jobs, parsed/index data, audit logs, and query logs.
- JWT auth, password hashing, `/auth/login`, `/auth/me`, `get_current_user`, and `require_admin`.
- Admin document upload, index, reindex, delete, and list endpoints.
- Authenticated document list, detail, structure, and page endpoints.
- Text, Markdown, and PDF parsing into normalized parsed-document data.
- Navigation index builder and PageIndex-style navigation adapter.
- LightRAG-only semantic retrieval; local semantic chunks and deterministic embedding fallback have been removed from runtime code.
- Retrieval router with `semantic`, `navigation`, `hybrid`, and `auto` modes; `RetrievalRoutingPolicy` selects local navigation versus LightRAG-backed retrieval; `LightRAGRetrievalStrategy` can combine LightRAG evidence with local navigation evidence for hybrid mode.
- Evidence-only retrieval via `POST /query/retrieve`.
- Answer composition via `POST /query/answer` and `POST /query`.
- Admin-only debug details when `include_debug=true`.
- Job table, job status endpoints, Redis `rq` enqueue path, and worker-owned job lifecycle.
- Audit/query log repositories and admin log endpoints.
- Seed admin, backup, and retrieval evaluation scripts.
- Interactive terminal UI: console scripts `context-engine` / `context-tui` (`cli.launcher`) driving `cli/tui/app.py` plus `cli/tui/` navigation, screens, and helpers; `cli/screens/` + `cli/renderers/` supply composable layouts; `cli/flows/` holds multi-step UX; all HTTP via `ApiClient` and `cli/services/`.
- Remote LightRAG integration for semantic retrieval/runtime, including HTTP adapter, domain manifest resolution, retrieval strategy, queued ingestion jobs, status refresh, and graph proxy routes.
- LightRAG domain deployment control behind `LIGHTRAG_DEPLOY_ENABLED`, including managed domain manifest, generated domain env files, generated compose file, fakeable Docker Compose runner, admin APIs in `app/api/routes/lightrag_admin.py`, user-safe `GET /lightrag/domains`, domain-aware upload/query selection, per-domain PostgreSQL storage metadata, and matching TUI/admin service wrappers.
- LightRAG provider configuration contract for generated `domain.env` files, including `LLM_BINDING*`, `EMBEDDING_BINDING*`, and `OPENAI_LLM_*` tuning fields sourced from root `LIGHTRAG_*` settings.
- Bedrock OpenAI-compatible support path by keeping LightRAG bindings as `openai` and setting `LIGHTRAG_LLM_BINDING_HOST` to `https://bedrock-runtime.<region>.amazonaws.com/openai/v1`.
- Provider secret boundary enforcement: provider API keys are emitted only to per-domain `domain.env` files and are not written into compose output, manifest JSON, or admin/user domain API responses.
- Contract files under `external/lightrag/contract/`.
- Behavior tests for API, terminal client (launcher, settings, TUI, services, API client, screen renderers, query payload), routing policy, LightRAG adapter, LightRAG deploy stack, auth guardrails, upload, retrieval, answer flow, queued jobs, and worker failure handling.
- Canonical document-processing scaffolding for `DocumentStructure`, pages, sections, blocks, source chunks, assets, structure quality, storage paths, and document-processing repository persistence.
- The LightRAG ingestion job now uses the existing upload/job flow to build and persist canonical `DocumentStructure` plus `SourceChunk` rows for parseable text/Markdown uploads, and it can use the real `DoclingParser` boundary for PDFs when Docling is installed. Built Source Chunks include section title/path metadata and section-prefixed chunk text that is forwarded to LightRAG alongside document, section, block, page, and asset IDs. Structure-processing failures fail ingestion explicitly (no raw LightRAG upload fallback).
- Document asset extraction saves assets, generates resized thumbnails when Pillow can read the asset, computes content hashes, extracts figure/image/table snapshots when Docling exposes image data, and deduplicates identical asset payloads while preserving per-occurrence metadata links.
- The Docling parser normalizes label variants (for example `section-header`), uses provenance fallback when primary page numbers are missing, and carries detached caption blocks into subsequent image/table assets when item-level caption APIs are empty.
- TOC refinement supports `auto`, `always`, and `never` modes, enforces bounded extractor calls, can parse common TOC text lines deterministically when no candidate sections are injected, resolves logical-to-physical page offsets by matching section titles outside TOC pages, validates resolved section starts against normalized page text, preserves nested refined section hierarchy, assigns hierarchy-aware page ranges, assigns blocks/assets to the deepest matching refined section, and emits rejection warnings with validation accuracy/offset/section context.
- Authenticated document debug APIs now expose canonical structure data when available: `GET /documents/{document_id}/structure`, `GET /documents/{document_id}/structure-quality`, `GET /documents/{document_id}/sections/{section_id}`, `GET /documents/{document_id}/chunks/{chunk_id}`, `GET /documents/{document_id}/toc-refinement-report`, and authenticated asset/thumbnail streaming.
- Retrieval asset enrichment can resolve assets from LightRAG evidence using legacy `metadata.source_chunk_id`, chunk-ingest `metadata.chunk_id`, or returned `metadata.asset_ids`, then rank and limit assets using direct chunk links, block links, caption/query overlap, page proximity, and section proximity.
- CLI service wrappers and TUI/screen renderers now cover document structure quality, TOC refinement reports, canonical structure summaries, section detail, source chunk detail with metadata, document detail debug summaries, and admin wrappers/actions for structure rebuild and LightRAG reingest.

## LightRAG Runtime Behavior

`LIGHTRAG_ENABLED=true` is the required integration runtime. Tests may inject/fake the remote adapter boundary, but runtime semantic retrieval has no local fallback.

Runtime behavior:

- `auto`, `semantic`, and `hybrid` semantic retrieval use `LightRAGRemoteRetrievalEngine` and `LightRAGRemoteAdapter`; `hybrid` can add local navigation evidence.
- `navigation` retrieval remains local.
- Admin upload stores a local mirror record/file and enqueues `lightrag_ingest_document`.
- Uploads require a LightRAG domain manifest so requested domains are explicit and validated.
- Upload responses include the LightRAG ingestion job id; LightRAG status is tracked under `documents.metadata.lightrag`.
- `GET /graphs` and `GET /graph/label/...` proxy to the remote LightRAG service.
- LightRAG timeouts/connect failures become `503`; auth/upstream/invalid-response failures become `502`.

## Intentional Simplifications

- Startup table creation is used instead of Alembic migrations.
- SQL cleanup/smoke scripts live under `migrations/`; they are not yet an Alembic migration chain.
- Context Engine stores LightRAG metadata and navigation data only; LightRAG owns chunks, embeddings, vector indexes, and graph data.
- Current text/Markdown ingestion still uses `TextDoclingParser`, a lightweight stub. The `DoclingParser` boundary and asset extraction exist with focused fake Docling fixtures, but broader real-PDF fixture coverage remains pending.
- The TOC Refiner is still a bounded service scaffold with an injectable extractor, deterministic TOC-line parsing for common formats, title-matched logical-to-physical page offset resolution, normalized title/page start validation, hierarchy-aware range assignment, and merge/assigner services. A real LLM provider/prompt implementation remains pending.
- Source Chunk ingestion is production-wired through `StructureAwareChunkBuilder`, including section-aware grouping, page ranges, inherited assets, section title/path metadata, section-prefixed chunk text, and caption text for asset-only chunks. Better sizing/tuning against real Docling output remains pending.
- The answer composer is deterministic, citation-focused, and evidence-bound. Missing or weak evidence returns an explicit no-evidence response; there is no general fallback answer mode. A real LLM provider can be added behind the same composer/provider boundary.
- Document ACLs are deferred; authenticated users can read ready documents.
- LightRAG domain deployment control is opt-in and generates a separate `.data/lightrag/docker-compose.lightrag-domains.yml`; generated domain services share the root Docker network.
- `LIGHTRAG_API_KEY` and `LIGHTRAG_LLM_BINDING_API_KEY` have distinct responsibilities: the former authenticates Context Engine -> LightRAG server traffic, while the latter authenticates LightRAG -> model provider traffic.

## Next Hardening Items

- Add Alembic migrations.
- Add rate limiting middleware and stronger request-size controls.
- Expand evaluation datasets and retrieval metrics.
- Add richer LightRAG status polling, database provisioning operations, and fuller TUI forms for domain create/start/stop/remove operations.
- Harden real-PDF Docling fixtures (table/figure/caption variation coverage) and tune parser normalization against real outputs.
- Add a real JSON-only LLM TOC extractor provider behind the current bounded refiner boundary.
- Tune `StructureAwareChunkBuilder` sizing and text-shaping against real Docling outputs.

