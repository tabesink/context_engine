# Context Engine Final Architecture Implementation Plan

## Target Outcome

Refactor the `v1` branch into a leaner architecture with fewer overlapping concepts and clearer ownership boundaries.

The final architecture should follow this rule:

```text
Documents = uploaded files + parsed local structure
Domains   = LightRAG runtime/workspace identity
Operations = all async/global visibility
Provider config = environment/domain-level configuration unless explicitly retained as runtime-admin editable
Frontend = typed API clients only, no scattered fetch calls
```

## Current Problems Being Solved

| Problem | Current Symptom | Target Fix |
|---|---|---|
| Duplicate status APIs | `ingestion-status` and `processing-status` both exist | Keep `processing-status` canonical |
| Duplicate async concepts | `/jobs` and `/operations` expose similar lifecycle state | Make `operations` the product/API concept |
| Domain source-of-truth ambiguity | DB rows, manifests, deploy services, and Docker state all express domain state | DB = desired metadata; Docker/health = observed runtime; manifest = generated artifact |
| Provider runtime complexity | DB profiles/secrets/defaults overlap with env/domain config | Use env/domain.env as source of truth for lean deployment |
| Upload workflow opacity | Upload touches storage, DB, parsing, chunks, assets, LightRAG, worker, polling | Explicit stages: register, parse, push, poll |
| Frontend coupling | Components can become tightly coupled to raw endpoints | Keep API calls inside typed API layer |

---

# Phase 0 — Safety Baseline and Inventory

## Objective

Freeze the current behavior before refactoring.

## Required Actions

1. Create a new branch from `v1`:

```bash
git checkout v1
git pull
git checkout -b refactor/final-lean-architecture
```

2. Add `docs/ARCHITECTURE_CURRENT.md` to the repo.
3. Document current route inventory from:

```text
app/main.py
app/api/routes/*.py
client/src/lib/api/*
client/src/api/*
```

4. Document current database ownership from:

```text
app/storage/models.py
app/storage/tables.py
alembic/versions/*
```

5. Capture existing frontend consumers of:

```text
ingestion-status
processing-status
/jobs
/operations
/admin/lightrag-*
/admin/lightrag-domains
/admin/ai-settings
```

## Deliverable

```text
docs/ARCHITECTURE_CURRENT.md
```

## Acceptance Criteria

- No functional code changes yet.
- Route inventory is complete.
- Frontend endpoint usage is mapped.
- Current tests still pass.

---

# Phase 1 — Canonicalize Document Status

## Objective

Make `processing-status` the only canonical document processing contract.

## Target Rule

```text
Use processing-status everywhere.
Keep ingestion-status only as a temporary compatibility alias.
```

## Backend Tasks

1. Locate endpoints:

```text
app/api/routes/documents.py
app/api/routes/admin.py
```

2. Keep canonical endpoints:

```text
GET /documents/{document_id}/processing-status
GET /admin/documents/{document_id}/processing-status
```

3. Keep deprecated wrappers temporarily:

```text
GET /documents/{document_id}/ingestion-status
GET /admin/documents/{document_id}/ingestion-status
```

4. Add comments above wrappers:

```python
# Deprecated: kept only for backward compatibility.
# Use /processing-status instead. Remove after frontend migration.
```

5. Ensure both wrappers internally call the same service method as `processing-status`.

## Frontend Tasks

Search for:

```text
ingestion-status
```

Replace with:

```text
processing-status
```

Relevant candidate areas:

```text
client/src/lib/api/admin-documents.ts
client/src/components/settings/*
client/src/components/chat/*
client/src/app/*
```

## Tests

Add or update tests to verify:

```text
/documents/{id}/processing-status returns current status
/admin/documents/{id}/processing-status returns current status for admin
/deprecated ingestion-status still works temporarily
frontend API client no longer uses ingestion-status
```

## Acceptance Criteria

- Frontend uses only `processing-status`.
- Deprecated endpoints still work but are not used by the UI.
- Status response is stable for queued, parsing, pushing, waiting_remote, succeeded, and failed states.

---

# Phase 2 — Make Operations the Canonical Async Visibility Layer

## Objective

Collapse the mental model of jobs and operations.

## Target Rule

```text
The database table may remain jobs.
The product/API concept should be operations.
```

## Backend Tasks

1. Treat `/operations` as the frontend/admin API.
2. Keep `/jobs` only for internal debugging or deprecate it.
3. Ensure every long-running action creates or maps to an operation:

```text
document upload / ingest
document reingest
document retry
domain create
domain start
domain stop
domain delete
provider test, if long-running
```

4. Normalize operation response shape:

```json
{
  "id": "uuid",
  "type": "document_ingest",
  "status": "queued|running|waiting_remote|succeeded|failed|cancelled",
  "stage": "register_upload|parse_local_structure|push_to_lightrag|poll_remote_indexing",
  "progress": 0,
  "resource_type": "document|domain|provider",
  "resource_id": "uuid-or-domain-id",
  "resource_label": "filename-or-domain-name",
  "actor_user_id": "uuid",
  "message": "Human readable current state",
  "error_message": null,
  "created_at": "iso-datetime",
  "updated_at": "iso-datetime"
}
```

5. If existing `JobRow` does not include all fields, derive missing fields from metadata before considering migrations.

## Frontend Tasks

1. Create or update:

```text
client/src/lib/api/operations.ts
```

2. Make admin activity/status UI consume `/operations` only.
3. Remove UI calls to `/jobs` unless there is a developer-only debug panel.

## Tests

Verify:

```text
GET /operations lists document ingest operations
GET /operations/{id} returns detail
Retry uses operation endpoint or cleanly delegates to job service
Non-admin users cannot see global operations
```

## Acceptance Criteria

- UI exposes Operations, not Jobs.
- `/jobs` is not used by normal frontend flows.
- One admin-visible table can show all multi-user async activity.

---

# Phase 3 — Simplify LightRAG Domain Lifecycle

## Objective

Reduce domain lifecycle to the four operations actually needed by the app.

## Target Rule

```text
Allowed lifecycle actions:
create
start
stop
delete
```

## Remove or Hide From UI

```text
repair
recreate
regenerate
purge
archive, unless delete maps to archive internally
view logs from More menu, unless logs page remains intentionally supported
upload document from domain More menu
view documents from domain More menu
```

## Backend Tasks

1. Consolidate admin domain route usage around one route family, preferably:

```text
GET    /admin/domains
POST   /admin/domains
GET    /admin/domains/{domain_id}
POST   /admin/domains/{domain_id}/start
POST   /admin/domains/{domain_id}/stop
DELETE /admin/domains/{domain_id}
```

2. If keeping existing route names for compatibility, make them delegate to the new domain service:

```text
/admin/lightrag-domains/* -> DomainService
/admin/lightrag/*         -> compatibility/debug only
```

3. Define source-of-truth rules:

```text
lightrag_domains DB row = desired domain metadata
Docker/HTTP health check = observed runtime state
manifest/domain.env = generated deployment artifact
operations = lifecycle transition history
audit_logs = who did what
```

4. Avoid adding more lifecycle-specific tables unless they provide unique query value.

## Frontend Tasks

1. Domain card/dropdown should expose only:

```text
Start
Stop
Delete
```

2. Remove from domain More menu:

```text
Upload document
View documents
View logs
Repair
Recreate
Regenerate
Purge
```

3. Move document upload/viewing to dedicated document route/page, not domain More menu.

## Tests

Verify:

```text
Admin can create/start/stop/delete domain
Non-admin cannot call lifecycle endpoints
Delete removes or disables the domain as intended
Domain operation appears in /operations
Domain list includes observed health/runtime state
```

## Acceptance Criteria

- Only create/start/stop/delete are visible in the UI.
- Domain source-of-truth rules are documented in code comments or architecture docs.
- Domain lifecycle actions create operation/audit records.

---

# Phase 4 — Clarify Provider Configuration Ownership

## Objective

Remove confusion between runtime DB settings and environment/domain-level provider config.

## Recommended Lean Target

For this 5–10 user app, prefer:

```text
.env / domain.env = source of truth
Provider UI = read-only diagnostics + optional health/test
Embedding model fixed per domain
Retrieval defaults not runtime-editable
LLM may vary per query only if already supported cleanly
```

## Backend Tasks

1. Decide whether DB provider profiles stay enabled.
2. If leaning static/env:
   - Keep existing tables for migration compatibility.
   - Stop using runtime defaults for retrieval defaults.
   - Resolve provider config from env/domain.env through a single service.
3. Create or clarify:

```text
ProviderConfigService
```

4. Ensure retrieval and ingestion call this service instead of reading from several places.

## Frontend Tasks

1. Provider page should become:

```text
Read-only current provider state
Embedding model for each domain
LLM provider health/test
Missing key / local mode indicators
```

2. Remove runtime-editable retrieval defaults.
3. Avoid showing provider fields that cannot be safely edited at runtime.

## Tests

Verify:

```text
Domain creation fails clearly if provider config is missing
Provider diagnostics endpoint returns current source/config mode
Retrieval does not mutate runtime defaults
Embedding model is fixed once domain is created
```

## Acceptance Criteria

- One provider source-of-truth is documented.
- UI no longer implies unsafe runtime editing if env owns config.
- Ingestion/retrieval resolve provider settings through one service path.

---

# Phase 5 — Document Upload Workflow Cleanup

## Objective

Make document upload understandable by separating logical stages.

## Target Stages

```text
register_upload
parse_local_structure
push_to_lightrag
poll_remote_indexing
```

## Backend Tasks

1. Keep the worker implementation if it is stable.
2. Rename or expose stages consistently in job/operation metadata.
3. Ensure `DocumentService.upload()` does only orchestration:

```text
validate request
save original file
create document row
create operation/job row
enqueue worker
return response
```

4. Move parsing/ingestion details into dedicated service methods:

```text
DocumentProcessingService.parse_local_structure()
LightRAGIngestionService.push_to_lightrag()
LightRAGStatusService.poll_remote_indexing()
```

5. Keep document state transitions explicit:

```text
uploaded -> parsing -> parsed -> pushing_to_lightrag -> waiting_remote -> ready
failed_parse / failed_lightrag / failed_remote
```

## Frontend Tasks

1. Upload UI should show:

```text
Queued
Parsing local structure
Sending to LightRAG
Waiting for LightRAG indexing
Ready
Failed
```

2. Poll only `processing-status`.
3. Use `operation_id` for admin/global activity view.

## Tests

Verify each stage can be represented and displayed.

## Acceptance Criteria

- Junior dev can read upload flow from route to worker without ambiguity.
- Status names are stable and mapped to user-facing labels.
- Upload response includes document id, operation id, and processing status URL.

---

# Phase 6 — Frontend API Layer Cleanup

## Objective

Prevent direct component-to-backend coupling.

## Target Rule

```text
Components call typed API helpers or stores.
Components do not directly hardcode backend URLs except in the API layer.
```

## Tasks

1. Search for direct fetch/axios usage:

```bash
grep -R "fetch(" client/src
```

2. Move raw backend calls into:

```text
client/src/lib/api/*
```

3. Create/normalize API modules:

```text
auth.ts
documents.ts
admin-documents.ts
retrieve.ts
domains.ts
operations.ts
provider.ts
users.ts
```

4. Keep state stores focused:

```text
auth-store.ts = auth/session only
lightrag-domain-store.ts = selected domain only
chat-session-store.ts = chat/session state only
settings-dialog-store.ts = UI state only
```

5. Avoid mixing remote fetching into presentational components.

## Acceptance Criteria

- All important backend calls are typed API functions.
- Components import API functions/stores, not endpoint strings.
- Domain selection has one store and one API source.

---

# Phase 7 — Database Ownership and Migration Guardrails

## Objective

Document which tables are core, optional, or candidates for deprecation.

## Classification

| Table | Target classification |
|---|---|
| users | Core |
| documents | Core |
| document_sections | Core if local navigation remains |
| document_pages | Core if page navigation remains |
| document_blocks | Core but heavy; preserve initially |
| document_assets | Core if evidence UI uses figures/tables |
| document_source_chunks | Core for citation/evidence mapping |
| jobs | Core internally, exposed as operations |
| audit_logs | Useful/core for admin app |
| query_logs | Useful, privacy-sensitive |
| lightrag_domains | Core |
| lightrag_domain_lifecycle | Candidate for deprecation if operations/audit replace it |
| ai_model_profiles | Optional if env owns provider config |
| ai_model_settings | Optional if env owns defaults |
| ai_provider_secrets | Optional if env owns secrets |

## Tasks

1. Do not drop tables immediately.
2. Mark candidate tables as deprecated in docs first.
3. Remove code reads before code writes.
4. Only then create migrations.
5. For each migration, include rollback instructions or a backup/export plan.

## Acceptance Criteria

- No destructive migration occurs without a documented read/write impact check.
- Any table removal has a preceding compatibility phase.

---

# Phase 8 — Test, Polish, and Documentation

## Objective

Lock in the lean architecture with tests and docs.

## Required Docs

```text
docs/ARCHITECTURE_TARGET.md
docs/API_CONTRACTS.md
docs/DOMAIN_LIFECYCLE.md
docs/DOCUMENT_UPLOAD_WORKFLOW.md
docs/OPERATIONS_VISIBILITY.md
docs/PROVIDER_CONFIG.md
```

## Required Test Categories

```text
Auth and role gating
Document upload
Document processing-status
Operations listing/detail
Domain lifecycle
Provider config diagnostics
Retrieval with valid/invalid domain filters
Frontend API client behavior
```

## Final Acceptance Criteria

```text
Only processing-status is used by frontend
Operations is the admin-visible async activity layer
Domain UI exposes only Start, Stop, Delete, plus Create elsewhere
Provider config source-of-truth is documented and enforced
Upload status stages are understandable and stable
Frontend backend calls are centralized in API layer
Junior dev can trace request flow from UI to backend to database/worker
```
