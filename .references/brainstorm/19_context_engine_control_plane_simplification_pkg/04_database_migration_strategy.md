# Database Migration Strategy

## Migration principles

Use expand-migrate-contract.

```text
Expand:   add new columns/tables while old code still works.
Migrate:  dual-write or backfill, update repositories/services.
Contract: remove old columns/names only after tests and frontend are stable.
```

## Why not a big bang migration?

The current schema has live code around `jobs`, `documents`, LightRAG lifecycle, and document navigation. A table rename without a compatibility period creates avoidable blast radius.

## Phase 1 migration: make jobs operation-compatible

Add operation-compatible columns to `jobs` first.

Columns:

```text
resource_type
resource_id
requested_by_user_id
progress_current
progress_total
started_at
finished_at
```

Backfill:

```sql
UPDATE jobs
SET resource_type = 'document', resource_id = document_id
WHERE document_id IS NOT NULL;

UPDATE jobs
SET resource_type = 'system'
WHERE document_id IS NULL AND resource_type IS NULL;
```

Later, optionally rename:

```text
jobs -> operations
```

But this rename is optional. If the team wants low migration risk, keep the physical table name `jobs` and use `OperationRow` as the ORM class name mapped to `__tablename__ = "jobs"` during transition.

## Phase 2 migration: promote LightRAG domains

Conservative path:

```text
rename lightrag_domain_lifecycle -> lightrag_domains
rename domain_id -> id
add display_name, health_status, base_url, container_name, host_port, embedding_profile_id, created_by_user_id
backfill display_name
add FK later after data audit
```

Data audit before FK:

```sql
SELECT DISTINCT d.lightrag_domain_id
FROM documents d
LEFT JOIN lightrag_domains lrd ON lrd.id = d.lightrag_domain_id
WHERE d.lightrag_domain_id IS NOT NULL
  AND lrd.id IS NULL;
```

Only add FK when this query returns zero rows or after intentionally creating missing domain rows.

## Phase 3 migration: duplicate document relationship arrays

First release:

- Stop writing to duplicate arrays.
- API reconstructs arrays from canonical relationships if still needed.

Second release:

- Drop duplicate columns.

Columns to drop later:

```text
document_sections.block_ids
document_sections.child_section_ids
document_blocks.asset_ids
document_source_chunks.asset_ids
```

Keep:

```text
document_source_chunks.block_ids
```

Reason: chunk-to-block can legitimately be many-to-many unless you introduce a join table such as `document_chunk_blocks`.

## Optional future migration: runtime settings

Do not rename `ai_model_settings` during the same refactor. It is low-value compared with domain/operation cleanup.

If renamed later:

```text
ai_model_settings -> runtime_settings
```

or keep as-is.
