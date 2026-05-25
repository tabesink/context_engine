# 09 — Testing and Migration Plan

## Test Groups

## 1. Storage Tests

```text
tests/storage/test_document_processing_repository.py
```

Cover:

```text
[ ] save/load DocumentStructure.pages
[ ] get_page()
[ ] missing page
[ ] resave replaces pages
```

## 2. API Tests

```text
tests/api/test_document_pages.py
tests/api/test_document_structure.py
tests/api/test_query_retrieve.py
tests/api/test_admin_document_reingest.py
```

Cover:

```text
[ ] Page API uses rich pages.
[ ] Structure API uses rich structure only.
[ ] Query retrieve uses RichNavigationEngine.
[ ] Admin reingest enqueues document_ingest.
```

## 3. Ingestion Tests

```text
tests/services/test_document_ingestion.py
tests/services/test_lightrag_ingestion_no_toc_refinement.py
```

Cover:

```text
[ ] ingestion saves rich structure
[ ] ingestion saves pages
[ ] ingestion builds source chunks
[ ] ingestion sends chunks to LightRAG
[ ] ingestion does not run TOC refinement
```

## 4. Job Tests

```text
tests/jobs/test_document_ingest_job.py
tests/api/test_jobs.py
```

Cover:

```text
[ ] one job kind
[ ] retry dispatches correctly
[ ] old job kinds are removed
```

## 5. Removal Tests / Grep Tests

Run:

```bash
rg "get_parsed|save_parsed|ParsedDocumentRow|NavigationIndexRow|get_navigation_index|save_navigation_index|PageIndexAdapter|NavigationRetrievalEngine|NavigationIndexBuilder|IndexingService|TocRefiner|TocRefinementReport"
```

Expected after final cleanup:

```text
No runtime references.
```

## Migration Sequence

## Migration 1

```text
add document_pages
optional backfill from parsed_documents
```

## Migration 2

```text
drop toc_refinement_reports
```

## Migration 3

```text
drop parsed_documents
drop navigation_indexes
```

Only run Migration 3 after the app no longer uses old tables.

## Verification Commands

```bash
alembic upgrade head
pytest
ruff check .
```

If used:

```bash
mypy .
```

## Manual Smoke Tests

```text
1. Start API.
2. Login as admin.
3. Upload document to LightRAG domain.
4. Confirm document_ingest job is created.
5. Confirm structure exists.
6. GET /documents/{id}/pages/1.
7. POST /query/retrieve mode=navigation.
8. POST /query/retrieve mode=semantic.
9. POST /query/retrieve mode=hybrid.
```
