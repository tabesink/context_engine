# Coding Agent Prompt: Remove Local Semantic Indexing and Make LightRAG the Only Semantic Retrieval Engine

You are a senior backend engineer working on `context_engine`.

Repository:

```text
https://github.com/tabesink/context_engine.git
```

## Selected architecture

Implement this direction:

```text
Option B — Context Engine keeps local navigation and document-control metadata.
LightRAG owns semantic retrieval completely.
LightRAG is always enabled.
There is no fallback local semantic retrieval mode.
```

## Critical rule

Do not save LightRAG embeddings in Context Engine PostgreSQL.

Do not save local fallback embeddings either.

The `semantic_chunks` table is old local fallback infrastructure. Stop using it first. Drop it in a later Alembic migration after no runtime code depends on it.

## Current code areas to inspect

Start with these files:

```text
app/services/indexing_service.py
app/indexing/semantic_index_builder.py
app/integrations/lightrag_adapter.py
app/services/document_service.py
app/integrations/lightrag_remote_adapter.py
app/retrieval/lightrag_remote_engine.py
app/retrieval/semantic_engine.py
app/retrieval/router.py
app/storage/tables.py
app/storage/repositories/documents.py
app/services/job_service.py
app/api/routes/documents.py
app/api/routes/query.py
app/core/config.py
.env.example
alembic/versions/*
tests/*
```

## Implementation goals

### 1. Make LightRAG mandatory

- Set `LIGHTRAG_ENABLED=true` as the expected runtime default.
- Add startup validation or clear runtime errors if LightRAG config is missing.
- Do not silently fall back to local semantic retrieval.

### 2. Make upload explicit

Update document upload so the request supports:

```text
target_engine="lightrag"
lightrag_domain_id="manuals"
```

Behavior:

- Only `target_engine="lightrag"` is accepted.
- Reject any local semantic target.
- Validate the LightRAG domain exists.
- Upload the document to the selected LightRAG domain.
- Store remote `document_id`, `track_id`, domain, status, and message in local document metadata.
- Queue optional local navigation/page processing only.

### 3. Remove local semantic indexing from runtime

In `app/services/indexing_service.py`:

- Remove import of `SemanticIndexBuilder`.
- Remove `self.semantic_builder`.
- Remove `semantic_builder.build(parsed)`.
- Remove `replace_semantic_chunks(...)`.
- Rename or narrow the service so it only handles local parsed pages and navigation indexes.

### 4. Preserve local navigation

Keep:

```text
DocumentParser
NavigationIndexBuilder
parsed_documents
navigation_indexes
```

The local parser/navigation system is allowed because it supports:

```text
- TUI document browsing;
- page inspection;
- structure inspection;
- debugging backend data shape.
```

But it must not create embeddings or semantic chunks.

### 5. Make LightRAG the only semantic retrieval engine

Update retrieval routing so:

```text
semantic mode -> LightRAGRemoteRetrievalEngine only
hybrid mode -> LightRAG semantic results plus optional local navigation evidence
navigation mode -> local page/navigation only
```

Remove runtime use of:

```text
SemanticRetrievalEngine
SemanticIndexBuilder
local LightRAGAdapter embed path
semantic_chunks reads/writes
```

If LightRAG is unavailable, return a clear error. Do not fall back.

### 6. Add status separation

Separate statuses:

```text
semantic status = LightRAG indexing status
navigation status = local parser/navigation status
```

Recommended metadata:

```json
{
  "target_engine": "lightrag",
  "lightrag": {
    "domain_id": "manuals",
    "document_id": "remote-doc-id",
    "track_id": "remote-track-id",
    "status": "indexing",
    "message": null
  },
  "local_processing": {
    "navigation_enabled": true,
    "navigation_status": "queued",
    "parsed_pages_available": false,
    "navigation_index_available": false
  }
}
```

### 7. Add status refresh

Add route/job:

```text
POST /documents/{document_id}/refresh-lightrag-status
```

It should:

- read local document metadata;
- call LightRAG status API using `track_id`;
- update local metadata;
- map remote success to local ready semantic state;
- map remote failure to local failed semantic state.

### 8. Remove dead code safely

After runtime removal and tests:

- delete or archive `app/indexing/semantic_index_builder.py`;
- delete or archive local `app/integrations/lightrag_adapter.py` if only used for fake/local embeddings;
- remove `SemanticChunkRow` from `app/storage/tables.py`;
- remove repository semantic chunk methods;
- create Alembic migration to drop `semantic_chunks`.

## Required tests

Add or update tests for:

```text
[ ] Upload accepts target_engine="lightrag".
[ ] Upload rejects any local semantic target.
[ ] Upload requires or resolves lightrag_domain_id.
[ ] Upload calls LightRAGRemoteAdapter.upload_document.
[ ] Upload stores remote document_id and track_id.
[ ] Upload does not write semantic_chunks.
[ ] Navigation processing stores parsed_documents and navigation_indexes only.
[ ] Semantic query calls LightRAGRemoteRetrievalEngine.
[ ] Semantic query does not instantiate local SemanticRetrievalEngine.
[ ] LightRAG failure returns clear error, no fallback.
[ ] Status refresh updates LightRAG metadata.
[ ] Alembic migration drops semantic_chunks after code references are removed.
```

## Acceptance criteria

The refactor is complete when:

```text
[ ] No runtime code imports SemanticIndexBuilder.
[ ] No runtime code imports local fake embedding adapter.
[ ] No runtime code writes semantic_chunks.
[ ] No runtime code reads semantic_chunks.
[ ] Upload is explicit: target_engine="lightrag", lightrag_domain_id="...".
[ ] LightRAG is required for semantic retrieval.
[ ] Local navigation/page browsing still works.
[ ] TUI/API shows LightRAG semantic status separately from local navigation status.
[ ] semantic_chunks table is dropped in a later migration.
[ ] Documentation says Context Engine does not store embeddings.
```
