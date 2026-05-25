# 10 — Coding Agent Prompt

Copy/paste this prompt into a coding agent.

```markdown
You are working in `https://github.com/tabesink/context_engine.git`.

Goal:
Make the codebase leaner by finishing the single rich navigation migration and removing duplicate local navigation and TOC-refinement paths.

Important architecture:
- LightRAG is the only semantic retrieval engine.
- The backend owns deterministic local navigation only.
- Rich `DocumentStructure` is the only local navigation source of truth.
- `DocumentStructure` must include persisted pages, sections, blocks, source_chunks, and assets.
- Do not add local embeddings.
- Do not add local semantic fallback.
- Do not keep permanent runtime fallback to `parsed_documents` or `navigation_indexes`.
- Do not call an LLM for TOC refinement.

Start with stabilization:
1. Verify or add `DocumentPageRow`.
2. Verify or add `DocumentPage.metadata`.
3. Make `DocumentProcessingRepository.save_structure()` save pages.
4. Make `DocumentProcessingRepository.get_structure()` load pages.
5. Add `DocumentProcessingRepository.get_page()`.

Then finish runtime wiring:
6. Change page API to read from `DocumentProcessingRepository.get_page()`.
7. Change structure API to use rich `DocumentStructure` only.
8. Wire `RetrievalService` to `RichNavigationEngine`.
9. Remove old `NavigationRetrievalEngine` and `PageIndexAdapter` references.

Then remove TOC refinement:
10. Remove `TocRefiner` from ingestion.
11. Remove TOC refinement report table/repository/API/schema.
12. Remove `enable_toc_refinement` request fields.

Then collapse jobs:
13. Replace `index_document`, `navigation_process_document`, and `lightrag_ingest_document` with one `document_ingest` job.
14. Fix job retry so it reruns the correct job kind.
15. Remove old `IndexingService` if no longer used.

Then simplify API:
16. Upload should require only file + `lightrag_domain_id`.
17. Admin document actions should become `reingest`, `refresh-status`, and `delete`.
18. Keep only `POST /query/retrieve` for retrieval; remove/deprecate `/query` and `/query/answer` if no real LLM answer generation is owned by this backend.

Add tests:
- page persistence
- page API
- structure API
- rich navigation retrieval
- no TOC refinement
- one document_ingest job
- job retry
- no old navigation runtime references

Before final response, run:
- alembic upgrade head
- pytest
- ruff check .
- mypy . if the repo uses mypy

In final response, report:
- changed files
- migrations
- removed code paths
- updated tests
- any remaining TODOs
```
