# Phase-by-Phase Implementation Plan

## Phase 0 — Baseline inventory and safety net

### Goal

Confirm the current schema, current routes, tests, and repository/service owners before changing DB structure.

### Tasks

1. Inspect current ORM:
   - `app/storage/tables.py`
   - `app/domain/models.py`

2. Inspect current migrations:
   - `migrations/alembic/versions`

3. Search the repo for these symbols and table names:

```bash
rg "JobRow|jobs|JobStatus|document_id" app tests migrations
rg "LightRAGDomainLifecycleRow|lightrag_domain_lifecycle|domain_lifecycle" app tests migrations
rg "block_ids|child_section_ids|asset_ids" app tests migrations
rg "ai_model_settings|AIModelSettingsRow" app tests migrations
```

4. Run baseline checks:

```bash
pytest
python -m alembic -c migrations/alembic.ini current
python -m alembic -c migrations/alembic.ini upgrade head
```

Adjust the Alembic command path if this repo uses a different invocation.

### Deliverables

- `docs/architecture/control_plane_state_ownership.md`
- A short inventory of all call sites for `jobs`, `lightrag_domain_lifecycle`, and duplicate document relationship arrays.

### Acceptance criteria

- Baseline tests pass before refactor work begins.
- There is a list of routes/services/repositories affected by the refactor.
- No schema changes yet.

---

## Phase 1 — Introduce state ownership contract and operation-compatible columns

### Goal

Make `jobs` able to represent any long-running work without breaking existing job code immediately.

### Why this is first

Renaming `jobs` to `operations` too early causes unnecessary blast radius. Add compatibility columns first, migrate service semantics, then rename later only when stable.

### Schema changes

Add to `jobs`:

```text
resource_type          string(32), nullable initially
resource_id            string(128), nullable initially
requested_by_user_id   string(36), nullable FK users.id
progress_current       integer, nullable
progress_total         integer, nullable
started_at             timestamptz, nullable
finished_at            timestamptz, nullable
```

Backfill:

```text
if document_id is not null:
  resource_type = "document"
  resource_id = document_id
else:
  resource_type = "system"
  resource_id = null
```

### Code changes

1. Add domain model enums/classes:

```text
OperationStatus = queued | running | succeeded | failed | canceled
OperationResourceType = document | domain | provider | system
```

2. Keep `JobStatus` as a compatibility alias for one phase.

3. Add repository methods:

```text
create_operation(...)
mark_operation_running(...)
mark_operation_succeeded(...)
mark_operation_failed(...)
list_operations(resource_type=None, resource_id=None, status=None)
```

4. Update ingestion code to create operations using:

```text
resource_type = document
resource_id = document_id
```

5. Update LightRAG domain operations to create operations using:

```text
resource_type = domain
resource_id = domain_id
```

### API guidance

Do not remove existing `/jobs` endpoints immediately.

Add or internally map:

```text
GET /api/operations
GET /api/operations/{operation_id}
```

Keep `/api/jobs` as an alias during the transition if frontend depends on it.

### Acceptance criteria

- Document ingestion still works.
- Domain lifecycle actions create operation rows.
- Existing job UI/API still works or is intentionally aliased.
- `jobs.document_id` is still present but no longer the only relationship mechanism.

---

## Phase 2 — Promote LightRAG domains to first-class rows

### Goal

Replace the concept of `lightrag_domain_lifecycle` with `lightrag_domains`.

### Target model

```text
lightrag_domains
  id
  display_name
  state
  health_status
  base_url
  container_name
  host_port
  embedding_profile_id
  error_message
  metadata
  created_by_user_id
  created_at
  updated_at
```

### Conservative migration path

Preferred low-risk path:

1. Rename table:

```text
lightrag_domain_lifecycle -> lightrag_domains
```

2. Rename primary key column:

```text
domain_id -> id
```

3. Add new nullable columns first.

4. Backfill `display_name` from `metadata.display_name` if available, else from `id`.

5. Add a FK from `documents.lightrag_domain_id` to `lightrag_domains.id` only after invalid domain strings are cleaned up.

### Code changes

1. Rename ORM class:

```text
LightRAGDomainLifecycleRow -> LightRAGDomainRow
```

2. Rename repositories/services around product concept:

```text
DomainLifecycleRepository -> LightRAGDomainRepository
DomainLifecycleService -> LightRAGDomainService
```

3. Normalize domain state names:

```text
creating | stopped | starting | running | stopping | failed | deleted
```

For a lean app exposing only Create / Start / Stop / Delete, this is enough.

### Acceptance criteria

- Domain list loads from `lightrag_domains`.
- Domain create/start/stop/delete update `lightrag_domains.state`.
- Domain actions create operation rows.
- Documents assigned to a domain are still queryable by `documents.lightrag_domain_id`.
- No UI route depends on `repair`, `recreate`, `regenerate`, or `purge` as normal user-facing lifecycle verbs.

---

## Phase 3 — Reduce duplicated document relationship state

### Goal

Stop maintaining redundant JSON reverse arrays where scalar relationships already exist.

### Current duplicated patterns

```text
document_sections.child_section_ids  duplicates document_sections.parent_section_id
document_sections.block_ids          duplicates document_blocks.section_id
document_blocks.asset_ids            duplicates document_assets.block_id
document_source_chunks.asset_ids     duplicates document_assets.chunk_id
```

### Recommended approach

Do not drop columns first. First stop writing to them. Then update read APIs to reconstruct lists from child tables.

### Step order

1. Add repository read helpers:

```text
list_sections_by_document(document_id)
list_blocks_by_section(document_id, section_id)
list_assets_by_block(document_id, block_id)
list_assets_by_chunk(document_id, chunk_id)
build_section_tree(document_id)
```

2. Update response builders to derive:

```text
child_section_ids = [child.id for child in sections_by_parent[parent_id]]
block_ids = [block.id for block in blocks_by_section[section_id]]
asset_ids = [asset.id for asset in assets_by_block[block_id]]
```

3. Stop ingestion from writing duplicate arrays.

4. Add tests proving the public API response is unchanged.

5. In a later migration, drop:

```text
document_sections.block_ids
document_sections.child_section_ids
document_blocks.asset_ids
document_source_chunks.asset_ids
```

### Acceptance criteria

- Existing document navigation UI still receives the same shape if needed.
- DB no longer has to maintain duplicate reverse arrays after final migration.
- Read performance remains acceptable for 5–10 users and local-network deployment.

---

## Phase 4 — Optional AI settings cleanup

### Goal

Keep AI provider tables stable but optionally rename `ai_model_settings` to a more general runtime settings name.

### Recommendation

Do not do this until Phases 1–3 are merged.

Options:

```text
Option A: Keep ai_model_settings. Lowest risk.
Option B: Rename to runtime_settings. Better future naming.
Option C: Convert to key/value app_settings. More flexible but less explicit.
```

My recommendation for your app right now:

```text
Keep ai_model_settings for now.
```

The complexity gain from renaming it is small compared with the risk of touching provider screens while domain/job refactors are active.

---

## Phase 5 — Final cleanup and deprecation removal

### Goal

Remove compatibility aliases and dead code after frontend and backend tests pass.

### Tasks

1. Remove old `Job` naming from public code where practical.
2. Keep DB table name `jobs` only if the migration risk of renaming is not worth it.
3. If renaming is desired:

```text
jobs -> operations
JobRow -> OperationRow
JobStatus -> OperationStatus
```

4. Remove normal UI exposure for:

```text
repair
recreate
regenerate
purge
view logs from the domain card More menu
upload/view documents from the domain lifecycle card
```

5. Keep backend-only emergency/admin scripts for repair-like maintenance if needed, but do not present them as normal lifecycle verbs.

### Final acceptance criteria

The app should expose a lean lifecycle vocabulary:

```text
Create Domain
Start Domain
Stop Domain
Delete Domain
Upload Document only from Documents surface
View Documents only from Documents surface
View Logs only from Jobs/Audit/Observability surface, not domain card More menu
```
