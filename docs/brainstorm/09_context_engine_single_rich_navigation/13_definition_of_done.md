# 13 — Definition of Done

This implementation is complete when all items below are true.

## Persistence

```text
[ ] `DocumentPage` is persisted in `document_pages`.
[ ] `DocumentProcessingRepository.save_structure()` saves pages.
[ ] `DocumentProcessingRepository.get_structure()` returns pages.
[ ] `DocumentProcessingRepository.get_page()` exists.
```

## APIs

```text
[ ] `GET /documents/{id}/pages/{n}` reads from rich pages.
[ ] `GET /documents/{id}/structure` has no `navigation_indexes` fallback.
[ ] `StructureResponse` includes pages.
[ ] TOC refinement report API is removed.
```

## Ingestion

```text
[ ] Runtime TOC refinement is removed.
[ ] `TocRefiner` is not instantiated during ingestion.
[ ] TOC refinement report storage is removed.
[ ] Ingestion still builds source chunks.
[ ] Ingestion still sends chunks to LightRAG.
```

## Retrieval

```text
[ ] `mode=navigation` uses `RichNavigationEngine`.
[ ] `mode=hybrid` combines LightRAG and rich navigation.
[ ] `PageIndexAdapter` is no longer used.
[ ] `NavigationRetrievalEngine` is removed or no longer referenced.
```

## Old Layer Removal

```text
[ ] New ingestion does not write `parsed_documents`.
[ ] New ingestion does not write `navigation_indexes`.
[ ] Runtime code has no old navigation references.
[ ] Old tables are dropped after safe migration.
```

## Tests

```text
[ ] Storage tests pass.
[ ] API tests pass.
[ ] Ingestion tests pass.
[ ] Retrieval tests pass.
[ ] Migration tests pass or are manually verified.
```

## Final Architecture

```text
Backend owns:
  deterministic navigation + citations + pages + sections + assets

LightRAG owns:
  semantic retrieval + graph retrieval
```

## Final Verification Commands

```bash
pytest
ruff check .
alembic upgrade head
```

Also run this grep check:

```bash
rg "get_parsed|save_parsed|ParsedDocumentRow|NavigationIndexRow|get_navigation_index|save_navigation_index|PageIndexAdapter|NavigationRetrievalEngine|NavigationIndexBuilder|TocRefiner|TocRefinementReport"
```

Expected result:

```text
No runtime references remain.
Only historical migration comments or deleted-code notes may remain.
```
