# 12 — Coding Agent Prompt

Use this prompt for the implementation agent.

```markdown
You are implementing a low-entropy navigation cleanup in `context_engine`.

Repository:
https://github.com/tabesink/context_engine.git

Goal:
Use only the rich `DocumentStructure` layer for local navigation. Persist `DocumentPage` as part of the rich structure. Remove optional LLM-based TOC refinement during ingestion. Remove the old simple `parsed_documents` + `navigation_indexes` navigation path after migration.

Important rules:
- Do not add local embeddings.
- Do not add local semantic fallback.
- Do not keep runtime fallback to `parsed_documents` or `navigation_indexes`.
- Do not call an LLM for TOC refinement.
- Keep LightRAG as the semantic retrieval owner.
- Keep backend local navigation deterministic.

Implement in phases:
1. Add `DocumentPageRow` and migration.
2. Save/load pages in `DocumentProcessingRepository`.
3. Remove TOC refinement path and API/report/table.
4. Change page API to read from rich pages.
5. Change structure API to use rich structure only.
6. Add `RichNavigationEngine`.
7. Wire retrieval service to use `RichNavigationEngine`.
8. Stop writing old local navigation data.
9. Drop old navigation tables/code after tests pass.

Add tests for:
- page persistence
- page API
- structure API
- no TOC refinement
- rich navigation retrieval
- hybrid retrieval still works
- no old navigation runtime references

Before final response, run:
- pytest
- ruff check .
- alembic upgrade head
- mypy . if this repo already uses mypy

Produce a summary of:
- changed files
- migrations
- tests added/updated
- removed old paths
- remaining TODOs
```
