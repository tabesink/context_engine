# 06 — Phase 3: Remove Optional LLM-Based TOC Refinement

## Goal

Make ingestion lighter and deterministic by removing runtime LLM-based TOC refinement.

## Files to Change

```text
app/services/lightrag_ingestion_service.py
app/document_processing/refinement.py
app/storage/repositories/document_processing.py
app/storage/tables.py
app/api/routes/documents.py
app/schemas/documents.py
tests/...
```

## Remove From `LightRAGIngestionService`

Remove imports:

```python
TocRefiner
TocRefinementResult
```

Remove constructor dependency:

```python
toc_refiner: TocRefiner | None = None
```

Remove field:

```python
self.toc_refiner = toc_refiner or TocRefiner()
```

Remove logic that decides:

```text
auto / always / never TOC refinement
```

Remove helper methods:

```python
_toc_refinement_mode()
_normalize_toc_refinement_mode()
```

## New Ingestion Flow

```text
LightRAGIngestionService.ingest_document()
    │
    ▼
parse structure
    │
    ▼
score quality deterministically
    │
    ▼
build source chunks
    │
    ▼
save rich structure locally
    │
    ▼
save artifacts
    │
    ▼
send source chunks to LightRAG
```

Keep deterministic quality scoring if useful:

```python
structure = structure.model_copy(update={"quality": self.quality_scorer.score(structure)})
```

Then:

```python
structure = self.chunk_builder.build(structure)
```

## Remove TOC Report Persistence

Recommended removals:

```text
TocRefinementReportRow
save_toc_refinement_report()
get_toc_refinement_report()
GET /documents/{document_id}/toc-refinement-report
TocRefinementReportResponse
enable_toc_refinement request option
```

Create a migration to drop:

```text
toc_refinement_reports
```

## Backward Compatibility

Ignore old metadata if present.

Do not expose new TOC refinement options in the API.

## Tests

```text
[ ] Ingestion does not instantiate `TocRefiner`.
[ ] Ingestion does not save a TOC refinement report.
[ ] Ingestion still saves `DocumentStructure`.
[ ] Ingestion still builds source chunks.
[ ] Ingestion still sends chunks to LightRAG.
[ ] TOC refinement API is removed or returns 404.
```

## Acceptance Criteria

```text
[ ] No runtime LLM TOC refinement path exists.
[ ] No TOC refinement API exists.
[ ] No TOC refinement table exists after migration.
[ ] Ingestion remains deterministic after parsing.
```
