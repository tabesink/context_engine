# 10 — Testing Plan

## Storage Tests

Create or update:

```text
tests/storage/test_document_processing_repository.py
```

Test:

```text
[ ] `save_structure()` persists pages.
[ ] `get_structure()` returns pages ordered by page number.
[ ] `get_page()` returns one page.
[ ] `get_page()` returns `None` for missing page.
[ ] Re-saving structure replaces old pages.
```

## API Tests

Create or update:

```text
tests/api/test_document_pages.py
tests/api/test_document_structure.py
```

Test:

```text
[ ] Page API reads from rich pages.
[ ] Page API does not require `parsed_documents`.
[ ] Missing page returns 404.
[ ] Missing document returns 404.
[ ] Structure API returns rich structure only.
[ ] Structure API includes pages.
[ ] Structure API does not fall back to `navigation_indexes`.
```

## Ingestion Tests

Create or update:

```text
tests/services/test_lightrag_ingestion_no_toc_refinement.py
```

Test:

```text
[ ] Ingestion does not instantiate `TocRefiner`.
[ ] Ingestion does not call `save_toc_refinement_report`.
[ ] Ingestion still saves structure.
[ ] Ingestion still builds source chunks.
[ ] Ingestion still sends source chunks to LightRAG.
```

## Retrieval Tests

Create:

```text
tests/retrieval/test_rich_navigation_engine.py
```

Test:

```text
[ ] Query matches section title.
[ ] Query matches source chunk.
[ ] Query matches block.
[ ] Query matches page text.
[ ] Evidence includes page range.
[ ] Evidence includes section title.
[ ] Evidence includes chunk/block/asset metadata.
[ ] Missing structure returns no evidence.
[ ] `top_k` is respected.
[ ] Hybrid retrieval combines LightRAG evidence and rich navigation evidence.
```

## Migration Tests

Create or manually verify:

```text
tests/migrations/test_document_pages_migration.py
tests/migrations/test_drop_old_navigation_tables.py
```

Test:

```text
[ ] Fresh DB migration works.
[ ] Existing old parsed pages can be backfilled.
[ ] Dropping old navigation tables works only after runtime references are removed.
```

## Manual Regression

```bash
pytest
ruff check .
alembic upgrade head
```

Manual API checks:

```text
GET /documents/{id}/structure
GET /documents/{id}/pages/1
POST /query/retrieve with mode=navigation
POST /query/retrieve with mode=semantic
POST /query/retrieve with mode=hybrid
```
