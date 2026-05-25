# 11 — Junior Developer Review Checklist

Use this checklist during code review.

## Page Persistence

```text
[ ] Is there a `DocumentPageRow`?
[ ] Does `DocumentPage` have `metadata`?
[ ] Does `save_structure()` save pages?
[ ] Does `get_structure()` load pages?
[ ] Does `get_page()` exist?
[ ] Are pages ordered by page number?
```

## API Behavior

```text
[ ] Page API reads from `DocumentProcessingRepository.get_page()`.
[ ] Page API does not call `get_parsed()`.
[ ] Structure API does not call `get_navigation_index()`.
[ ] Structure API returns pages.
[ ] Missing rich structure returns 404.
```

## Retrieval

```text
[ ] `RetrievalService` instantiates `RichNavigationEngine`.
[ ] `mode=navigation` uses rich structure.
[ ] `mode=hybrid` still works.
[ ] No `PageIndexAdapter` in runtime retrieval.
[ ] No `NavigationRetrievalEngine` in runtime retrieval.
```

## Ingestion

```text
[ ] Ingestion saves rich structure.
[ ] Ingestion saves pages.
[ ] Ingestion builds source chunks.
[ ] Ingestion sends chunks to LightRAG.
[ ] Ingestion does not run TOC refinement.
```

## Jobs

```text
[ ] There is one document ingestion job kind.
[ ] Retry dispatches correctly.
[ ] Old index/navigation jobs are removed.
```

## API Surface

```text
[ ] Upload does not expose `semantic_engine`.
[ ] Upload does not expose `process_navigation`.
[ ] Upload does not expose `enable_toc_refinement`.
[ ] Admin document actions are not duplicated.
[ ] Query endpoints are not duplicated.
```

## Final Grep

Run:

```bash
rg "get_parsed|save_parsed|ParsedDocumentRow|NavigationIndexRow|get_navigation_index|save_navigation_index|PageIndexAdapter|NavigationRetrievalEngine|NavigationIndexBuilder|IndexingService|TocRefiner|TocRefinementReport"
```

Review every match.
