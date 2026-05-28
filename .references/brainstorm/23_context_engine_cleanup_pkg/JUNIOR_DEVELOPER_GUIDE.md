# Junior Developer Guide

## How to think about this codebase

This is not just a CRUD app. It coordinates:

- users and auth
- admin-only domain/document operations
- LightRAG runtime deployment
- document ingestion and job status
- retrieval/evidence responses
- frontend workspace/context displays

Cleanup should make those responsibilities easier to see, not remove them.

## Where to start reading

1. `README.md` — runtime assumptions.
2. `app/main.py` — FastAPI app setup.
3. `app/api/routes/` — public API surfaces.
4. `app/services/` — use-case logic.
5. `app/lightrag_deploy/` — LightRAG deployment/runtime mechanics.
6. `app/storage/` — database access.
7. `app/workers/` — background work/status polling.
8. `client/src/api/` — frontend API calls.
9. `client/src/hooks/` — frontend state/polling hooks.
10. `tests/` — expected behavior.

## Safe zones

Usually safer to change:

- documentation
- comments/docstrings
- UI labels/tooltips
- `.gitignore`
- frontend layout if API calls are unchanged
- test additions
- private helper extraction with strong tests

## Risky zones

Be careful with:

- auth dependencies
- admin permission checks
- purge/delete/archive behavior
- Postgres provisioning
- Docker/Compose generation
- environment variable names
- persistent storage paths
- migrations
- evidence response schemas
- document status enums
- frontend/backend contract types

## Where new changes should go

| Change type | Preferred location |
|---|---|
| New HTTP endpoint | `app/api/routes/<surface>.py` |
| New use-case behavior | `app/services/` or focused service in existing domain folder |
| LightRAG runtime mechanics | `app/lightrag_deploy/` |
| Database query | `app/storage/repositories/` |
| Schema/DTO | `app/schemas/` or domain-specific schema file |
| Background job | `app/workers/` and job service/repository |
| Frontend API call | `client/src/api/` |
| Frontend polling | `client/src/hooks/` |
| Shared UI card/table | `client/src/components/` |
| Feature-specific UI | `client/src/features/` or route-local component |

## Cleanup rules

1. Do not delete code because it looks ugly. First prove it is unused or duplicated.
2. Do not remove safety checks.
3. Do not change auth/permissions without tests.
4. Do not change env vars without updating `.env.example` and docs.
5. Do not change storage paths without migration/backup notes.
6. Do not change API response shapes without updating frontend types and tests.
7. Prefer renaming/hiding advanced actions before deleting them.
8. Prefer one small cleanup PR at a time.

## Mental model for LightRAG domain operations

Use this vocabulary:

- **Create**: define a new domain and its metadata/config.
- **Start**: run an existing domain runtime.
- **Stop**: stop runtime without deleting data.
- **Repair**: canonical safe recovery; regenerate/provision/restart/probe as needed.
- **Archive**: remove from active use while preserving data.
- **Purge**: permanently remove data/config after explicit confirmation.
- **Recreate**: compatibility/advanced Docker-level recovery; do not use as normal UX.
- **Regenerate**: internal/advanced artifact rewrite; do not use as normal UX.

## How to avoid adding entropy

Before adding a new file/function, ask:

1. Is there already a service that owns this concept?
2. Is this a domain concept or just a helper?
3. Will a junior developer know where to find this later?
4. Does this duplicate a frontend/backend contract?
5. Does this create another source of truth for status?
