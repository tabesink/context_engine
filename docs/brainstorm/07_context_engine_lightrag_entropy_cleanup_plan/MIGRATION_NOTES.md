# Migration Notes: Removing Local Semantic Persistence

## Purpose

The codebase currently contains local semantic persistence concepts such as `SemanticChunkRow` and repository methods for replacing/listing semantic chunks.

Because the desired architecture is remote LightRAG-only semantic retrieval, these concepts should not remain active runtime dependencies.

## Recommended staged migration

### Stage A — Stop runtime use

First PR should stop all runtime usage:

- Do not instantiate `SemanticIndexBuilder`.
- Do not call `replace_semantic_chunks()`.
- Do not call `list_semantic_chunks()`.
- Do not query `semantic_chunks` for retrieval.
- Do not write new local semantic chunks.

This stage can leave the DB table in place to avoid destructive schema changes while the runtime behavior is being cleaned.

### Stage B — Add Alembic migration

Once Stage A is merged and tested, add a migration to drop the table if it exists.

Migration should be explicit and reversible if practical:

```text
upgrade:
- drop semantic_chunks table

downgrade:
- recreate semantic_chunks table only if needed for rollback
```

Before dropping, confirm:

```bash
rg "SemanticChunkRow|semantic_chunks|replace_semantic_chunks|list_semantic_chunks"
```

Only migration history or deletion notes should remain.

## Data-loss note

Dropping `semantic_chunks` deletes local semantic chunk records.

That is acceptable only if:

- no production system depends on local semantic chunks;
- LightRAG already owns semantic retrieval;
- source chunks needed for navigation/grounding remain in `document_source_chunks` or equivalent structure-aware tables.

Do not drop source chunks, document blocks, sections, assets, pages, or navigation indexes.
