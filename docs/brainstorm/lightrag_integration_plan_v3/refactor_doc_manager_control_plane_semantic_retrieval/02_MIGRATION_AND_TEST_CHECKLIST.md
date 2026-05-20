# Migration and Test Checklist

## 1. Pre-migration code search checklist

Before dropping `semantic_chunks`, search for these strings:

```text
SemanticChunkRow
semantic_chunks
replace_semantic_chunks
list_semantic_chunks
SemanticIndexBuilder
LightRAGAdapter().embed
SemanticRetrievalEngine
```

No runtime code should depend on them.

## 2. Safe removal order

Use this order:

```text
1. Add LightRAG-only upload validation.
2. Make remote LightRAG upload the only upload target.
3. Remove semantic chunk creation from IndexingService.
4. Rename/narrow IndexingService to navigation processing.
5. Make LightRAGRemoteRetrievalEngine the only semantic retrieval engine.
6. Update tests.
7. Remove dead semantic code.
8. Remove ORM model.
9. Add Alembic migration to drop semantic_chunks.
10. Run full test suite.
```

## 2.1 Option 3 infrastructure order

Use this order before runtime LightRAG domain ingestion is considered production-ready:

```text
1. Validate the PostgreSQL image/build supports both vector and AGE extensions.
2. Add root settings for LightRAG provisioning admin DSN and generated runtime credential policy.
3. Create per-domain LightRAG database and limited runtime user during domain create.
4. Render domain.env with PGKVStorage, PGDocStatusStorage, PGGraphStorage, PGVectorStorage.
5. Put root services and generated LightRAG services on the shared Docker network.
6. Build LightRAG from external/lightrag using the repo-owned Dockerfile.
7. Verify domains.json contains no credentials.
```

## 3. Alembic migration checklist

Migration name:

```text
drop_semantic_chunks_table
```

Upgrade:

```python
op.drop_table("semantic_chunks")
```

Downgrade:

Either recreate the table or mark as destructive depending project convention.

Suggested downgrade if supported:

```python
op.create_table(
    "semantic_chunks",
    sa.Column("id", sa.String(length=64), primary_key=True),
    sa.Column("document_id", sa.String(length=36), nullable=False),
    sa.Column("chunk_index", sa.Integer(), nullable=False),
    sa.Column("text", sa.Text(), nullable=False),
    sa.Column("embedding", <json_type>, nullable=False),
    sa.Column("page_start", sa.Integer(), nullable=True),
    sa.Column("page_end", sa.Integer(), nullable=True),
    sa.Column("score_hint", sa.Float(), nullable=True),
    sa.Column("metadata", <json_type>, nullable=False),
)
```

If the project uses SQLite for tests and Postgres for production, ensure the JSON type helper is handled correctly.

## 4. Runtime validation checklist

```text
[ ] App starts with LIGHTRAG_ENABLED=true.
[ ] App refuses or clearly errors if LightRAG config is missing.
[ ] Admin can upload document with semantic_engine="lightrag".
[ ] Upload requires/uses lightrag_domain_id.
[ ] Document metadata stores LightRAG domain, remote document id, and track id.
[ ] No semantic_chunks are created.
[ ] Optional navigation processing creates parsed_documents.
[ ] Optional navigation processing creates navigation_indexes.
[ ] Query semantic mode calls remote LightRAG.
[ ] Query navigation mode does not call semantic chunks.
[ ] Query hybrid mode does not call semantic chunks.
[ ] LightRAG down produces clear error.
[ ] There is no local semantic fallback.
```

Option 3 runtime validation:

```text
[ ] LightRAG domain env contains WORKSPACE=<domain_id>.
[ ] LightRAG domain env contains POSTGRES_DATABASE=lightrag_<domain_id>.
[ ] LightRAG domain env selects PGKVStorage, PGDocStatusStorage, PGGraphStorage, PGVectorStorage.
[ ] domains.json does not contain database passwords or API keys.
[ ] Generated compose connects LightRAG domains to the same named network as postgres.
[ ] LightRAG API-key calls use X-API-Key.
[ ] A throwaway database can CREATE EXTENSION vector.
[ ] A throwaway database can CREATE EXTENSION AGE.
```

## 5. TUI validation checklist

```text
[ ] Upload screen asks for LightRAG domain.
[ ] Upload screen does not ask for local semantic mode.
[ ] Document detail screen shows LightRAG status.
[ ] Document detail screen shows navigation status separately.
[ ] Query screen requires or clearly selects domain.
[ ] Query screen shows remote LightRAG errors clearly.
```

Upload API validation:

```text
[ ] Upload accepts semantic_engine="lightrag".
[ ] Upload rejects semantic_engine values other than lightrag.
[ ] Upload stores detailed status under metadata.lightrag and metadata.navigation.
[ ] Navigation state is not stored under metadata.local_processing.
```

## 6. Concurrency validation checklist

```text
[ ] Multiple users can query same LightRAG domain.
[ ] Admin can upload while users query.
[ ] Existing ready documents remain queryable during new document indexing.
[ ] Same-domain simultaneous uploads are locked, queued, or rejected clearly.
[ ] Failed LightRAG upload does not corrupt local document list.
```

## 7. Final proof checklist

Run:

```text
pytest
```

Then manually verify:

```text
[ ] No semantic_chunks table after migration.
[ ] No SemanticChunkRow ORM model.
[ ] No semantic_index_builder runtime import.
[ ] No local embedding adapter runtime import.
[ ] LightRAG is the only semantic retrieval path.
```
