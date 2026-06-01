# Post-Implementation Handoff

This handoff captures the work completed from the current-code lean architecture refactor plan so the next agent can continue without reconstructing the prior context.

## What Was Implemented

The implementation followed the locked current-code direction:

- Provider config stays hybrid: DB-backed AI profiles/secrets are admin-managed runtime configuration, env remains bootstrap/fallback, and generated `domain.env` files are deployment snapshots.
- Operations are now the product/API async concept.
- The `jobs` table remains the internal storage/worker implementation detail.
- Public document processing stages now use explicit workflow vocabulary.
- CLI fallout was intentionally not addressed because repo guidance says CLI is unsupported unless explicitly excepted.

## Key Code Changes

### Operations API

Changed `app/api/routes/operations.py` and `app/schemas/jobs.py` so `/operations` exposes product-shaped fields:

- `type`
- `status`
- `stage`
- `progress`
- `resource_type`
- `resource_id`
- `resource_label`
- `actor_user_id`
- `message`
- `error_message`
- timestamps

Added:

- `POST /operations/{operation_id}/retry`

Removed:

- `/jobs` router registration from `app/main.py`
- `app/api/routes/jobs.py`

Important compatibility note: the DB table and repository are still named `jobs`. Do not rename the table in the next phase unless you also plan a migration and broader storage compatibility work.

### Upload And Retry Responses

Changed `app/api/routes/admin.py` and `app/schemas/documents.py`:

- Upload/retry responses now expose `operation_id`.
- `job_id` was removed from the public upload response model.
- `POST /admin/documents/{document_id}/reingest` now returns `operation_id`.

### Explicit Stage Vocabulary

Changed:

- `app/services/job_service.py`
- `app/workers/tasks.py`
- `app/services/document_ingestion_status_service.py`
- `app/services/processing_status_service.py`

Public stages now use:

- `register_upload`
- `parse_local_structure`
- `push_to_lightrag`
- `poll_remote_indexing`
- `complete`
- `failed`

Current implementation note: domain lifecycle operations use `push_to_lightrag` as the running stage for lifecycle work. If the next phase wants cleaner domain-specific semantics, introduce a broader operation-stage taxonomy deliberately rather than ad hoc stage names.

### Domain Lifecycle Operations

Changed `app/api/routes/lightrag_admin.py`:

- Domain create/start/stop/delete now create operation rows.
- Operation success/failure is recorded around the existing deployment service calls.
- Docker/manifest mechanics remain inside `app/lightrag_deploy/service.py`.
- Audit logging is preserved.

Risk note: GitNexus impact marked `LightRAGDomainService` as MEDIUM risk. The implementation intentionally avoided changing that service’s deployment internals.

### Frontend API Layer

Added:

- `client/src/lib/api/operations.ts`

Updated:

- `client/src/lib/api/admin-documents.ts` no longer includes `job_id` on upload response types.

No operations UI was added in this pass. The next agent can build UI against `operationsApi.list`, `operationsApi.get`, and `operationsApi.retry`.

### Documentation

Added:

- `docs/ARCHITECTURE_CURRENT.md`
- `docs/PROVIDER_CONFIG.md`

Updated:

- `docs/architecture/upload_status_state_ownership.md`
- `docs/architecture.md`
- `docs/implementation-status.md`
- `docs/deployment.md`
- `docs/adr/0003-indexing-job-model.md`

The historical brainstorm plan was not edited.

## Verification Performed

Passed:

```powershell
python -m pytest tests/test_api.py -k "operations or processing_status or retry or lightrag_domain_routes or upload_queues_lightrag"
```

Result: `9 passed`

Passed:

```powershell
python -m pytest tests/test_api.py -k "operations or retry"
```

Result: `5 passed`

Passed:

```powershell
python -m pytest tests/test_ai_settings_api.py tests/test_ai_model_settings_service.py tests/test_ai_provider_secrets.py tests/test_model_profile_resolver.py
```

Result: `18 passed`

Passed frontend lint for edited API files:

```powershell
npm run lint -- --file src/lib/api/operations.ts --file src/lib/api/admin-documents.ts
```

Also checked IDE lints for edited backend/frontend files; no linter errors were reported.

## Known Test Caveat

A full `python -m pytest tests/test_api.py` run was not green in this session. The failures were dominated by test isolation/state leakage rather than the focused refactor path:

- The suite reuses `.data/test_context_engine.db` across pytest invocations.
- `test_auth_me_rejects_inactive_user` leaves `user@example.com` inactive, causing many later auth-dependent tests to return `401`.
- Re-running selected tests after deleting `.data/test_context_engine.db` passed.

Next agent should either fix the test isolation issue before relying on full-suite signal, or run the focused slices from a clean DB while changing nearby behavior.

## Git/Workspace Notes

There were pre-existing unrelated working-tree changes before this implementation. Do not revert them without user approval. Notable unrelated areas observed in `git status` included:

- `.dockerignore`
- `AGENTS.md`
- `CLAUDE.md`
- `client/next-env.d.ts`
- `client/src/app/login/page.tsx`
- `client/src/features/graph/GraphViewer.tsx`
- `client/src/stores/auth-store.ts`
- deployment scripts
- `.references/cli/`

The implementation-generated pycache files and `.data/test_context_engine.db` were cleaned up after test runs.

## Recommended Next-Agent Path

Suggested skills:

- `tdd` for vertical behavior slices.
- `gitnexus-impact-analysis` before editing shared symbols.
- `gitnexus-exploring` if tracing unfamiliar flows.

Recommended next steps:

1. Fix or isolate the full `tests/test_api.py` state leakage so broad regression checks become trustworthy.
2. Build an operations UI, if desired, using `client/src/lib/api/operations.ts` and the design rules in `DESIGN.md`.
3. Decide whether domain lifecycle stages need domain-specific public names or whether the current generic operation stages are acceptable.
4. Keep CLI tests/docs out of scope unless the user explicitly grants a CLI exception.
5. Before any further symbol edits, run GitNexus impact on the target symbol and report the blast radius.

