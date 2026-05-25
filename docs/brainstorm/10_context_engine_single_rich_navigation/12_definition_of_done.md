# 12 — Definition of Done

## Rich Structure

```text
[ ] `DocumentPage` is persisted in `document_pages`.
[ ] `DocumentStructure.pages` survives save/load.
[ ] Pages are returned in deterministic order.
[ ] `DocumentProcessingRepository.get_page()` exists.
```

## APIs

```text
[ ] `GET /documents/{id}/pages/{n}` reads rich pages.
[ ] `GET /documents/{id}/structure` reads rich structure only.
[ ] Structure response includes pages.
[ ] TOC refinement report API is removed.
[ ] Upload API has no old optional navigation/semantic/TOC switches.
```

## Retrieval

```text
[ ] `RichNavigationEngine` is live.
[ ] Old `NavigationRetrievalEngine` is not used.
[ ] Old `PageIndexAdapter` is not used.
[ ] `mode=navigation` returns rich evidence.
[ ] `mode=hybrid` merges LightRAG + rich navigation.
```

## Ingestion

```text
[ ] Ingestion uses one deterministic flow.
[ ] Ingestion saves rich structure.
[ ] Ingestion sends chunks to LightRAG.
[ ] No LLM-based TOC refinement exists.
```

## Jobs

```text
[ ] One job kind: `document_ingest`.
[ ] Job retry is correct.
[ ] Old index/navigation job methods are removed.
```

## Old Stack Removed

```text
[ ] `parsed_documents` removed after migration.
[ ] `navigation_indexes` removed after migration.
[ ] `IndexingService` removed if no longer used.
[ ] `NavigationIndexBuilder` removed.
[ ] `PageIndexAdapter` removed.
[ ] `NavigationRetrievalEngine` removed.
```

## Commands Pass

```bash
alembic upgrade head
pytest
ruff check .
```

If applicable:

```bash
mypy .
```

## Final Architecture

```text
Context Engine:
  deterministic local navigation over DocumentStructure

LightRAG:
  semantic + graph retrieval

No duplicate local navigation layer.
No local semantic fallback.
No optional LLM TOC refinement.
```
