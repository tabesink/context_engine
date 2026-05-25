# 02 — Current State Evidence Checklist

Before coding, inspect these files in the repository.

## Rich model

```text
app/document_processing/models.py
```

Expected current finding:

```text
DocumentPage exists.
DocumentStructure.pages exists.
```

## Rich repository

```text
app/storage/repositories/document_processing.py
```

Expected current finding:

```text
Repository saves/loads sections, blocks, source_chunks, assets.
Repository does not fully persist/load DocumentStructure.pages.
```

## Storage tables

```text
app/storage/tables.py
```

Expected current finding:

```text
ParsedDocumentRow exists.
NavigationIndexRow exists.
Rich section/block/chunk/asset rows exist.
DocumentPageRow is missing.
```

## Page API

```text
app/api/routes/documents.py
```

Expected current finding:

```text
GET /documents/{document_id}/pages/{page_number}
reads from DocumentRepository.get_parsed().
```

## Structure API

```text
app/api/routes/documents.py
```

Expected current finding:

```text
GET /documents/{document_id}/structure
tries rich DocumentStructure first,
then falls back to old navigation_indexes.
```

## Local navigation retrieval

```text
app/retrieval/navigation_engine.py
app/integrations/pageindex_adapter.py
```

Expected current finding:

```text
NavigationRetrievalEngine loads parsed pages and navigation index.
PageIndexAdapter does deterministic keyword matching over page text/title.
```

## TOC refinement

```text
app/services/lightrag_ingestion_service.py
app/document_processing/refinement.py
```

Expected current finding:

```text
TocRefiner is wired into ingestion.
TOC refinement can run in optional modes.
```

## TOC report API/schema

```text
app/api/routes/documents.py
app/schemas/documents.py
app/storage/repositories/document_processing.py
app/storage/tables.py
```

Expected current finding:

```text
TOC refinement report route/schema/table/repository helpers exist.
```
