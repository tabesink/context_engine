# Test Plan

## Phase 0 tests

Run existing suite:

```bash
pytest
```

Run migration head:

```bash
python -m alembic -c migrations/alembic.ini upgrade head
```

Adjust command if repo uses `alembic.ini` at root.

## Phase 1 operation tests

Add tests for:

```text
create_operation with document resource
create_operation with domain resource
operation status transitions
operation failure captures error_message
operation list filters by resource_type/resource_id/status
legacy job endpoint still works or is intentionally replaced
```

Minimum test cases:

```python
async def test_document_ingest_creates_document_operation(): ...
async def test_domain_start_creates_domain_operation(): ...
async def test_operation_status_rollup_updates_document_status(): ...
async def test_operation_status_rollup_updates_domain_state(): ...
async def test_legacy_jobs_endpoint_maps_to_operations_temporarily(): ...
```

## Phase 2 domain table tests

Add tests for:

```text
domain create writes lightrag_domains row
domain start changes state through service
domain stop changes state through service
domain delete marks deleted or removes row according to product decision
document domain assignment references existing domain
invalid domain_id rejected on new uploads
```

Suggested tests:

```python
async def test_create_domain_persists_first_class_domain_row(): ...
async def test_document_upload_rejects_unknown_domain_id(): ...
async def test_domain_delete_blocks_or_handles_existing_documents(): ...
```

Important product decision for delete:

```text
If domain has documents, should delete be blocked, soft-delete domain, or mark documents deleted?
```

Recommended lean behavior:

```text
Block hard delete if documents exist.
Use soft delete/deleted state first.
```

## Phase 3 document structure tests

Add tests for:

```text
section tree can be reconstructed from parent_section_id
blocks can be listed by section_id
assets can be listed by block_id/chunk_id
API response remains compatible if UI expects child_section_ids/block_ids/asset_ids
```

Suggested tests:

```python
def test_section_tree_derived_from_parent_pointers(): ...
def test_block_ids_derived_from_blocks_table(): ...
def test_asset_ids_derived_from_assets_table(): ...
def test_ingestion_does_not_need_duplicate_reverse_arrays(): ...
```

## Migration tests

For each migration:

```bash
python -m alembic -c migrations/alembic.ini upgrade head
python -m alembic -c migrations/alembic.ini downgrade -1
python -m alembic -c migrations/alembic.ini upgrade head
```

If downgrade is not supported in this project, document that clearly in the migration file.

## End-to-end smoke tests

Manual smoke test sequence:

```text
1. Create admin user.
2. Create LightRAG domain.
3. Start domain.
4. Upload document to domain from Documents surface.
5. Confirm operation appears in Operations/Jobs surface.
6. Confirm document moves uploaded -> indexing -> ready or failed.
7. Query domain.
8. Stop domain.
9. Delete domain only when safe.
```
