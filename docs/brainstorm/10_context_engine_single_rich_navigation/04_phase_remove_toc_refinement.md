# 04 — Phase: Remove LLM-Based TOC Refinement

## Goal

Remove optional LLM-based TOC refinement during ingestion to make the system lighter, deterministic, and easier to debug.

## Files to Inspect/Change

```text
app/services/lightrag_ingestion_service.py
app/document_processing/refinement.py
app/document_processing/models.py
app/storage/tables.py
app/storage/repositories/document_processing.py
app/api/routes/documents.py
app/schemas/documents.py
tests/...
```

## Remove From Ingestion

Remove:

```text
TocRefiner
TocJsonExtractor
TocRefinementResult
_toc_refinement_mode()
_normalize_toc_refinement_mode()
toc_refiner constructor arg
self.toc_refiner = ...
conditional refine branch
save_toc_refinement_report()
```

## Target Ingestion Flow

```text
parse structure
   │
   ▼
score structure quality deterministically
   │
   ▼
build source chunks
   │
   ▼
save DocumentStructure
   │
   ▼
save artifacts
   │
   ▼
send source chunks to LightRAG
```

## Remove Public TOC Report Surface

Remove:

```text
GET /documents/{document_id}/toc-refinement-report
TocRefinementReportResponse
TocRefinementReportRow
get_toc_refinement_report()
save_toc_refinement_report()
```

## Remove Request Fields

Remove:

```text
enable_toc_refinement
```

from upload/rebuild/reingest request schemas or form fields.

## Clean Models

Remove or simplify fields like:

```text
DocumentSection.source = "toc_refiner"
StructureQuality.should_run_toc_refiner
```

Keep deterministic quality diagnostics if useful.

## Tests

```text
[ ] Ingestion does not instantiate TocRefiner.
[ ] Ingestion does not call save_toc_refinement_report.
[ ] Ingestion still saves structure.
[ ] Ingestion still builds source chunks.
[ ] Ingestion still sends source chunks to LightRAG.
[ ] TOC report route is removed.
[ ] TOC report table is dropped by migration.
```

## Acceptance Criteria

```text
[ ] No runtime LLM TOC refinement exists.
[ ] No TOC refinement route/schema/table exists.
[ ] No user/admin option can enable TOC refinement.
```
