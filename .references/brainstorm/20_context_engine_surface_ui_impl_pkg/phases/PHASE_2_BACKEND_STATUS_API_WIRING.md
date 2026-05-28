# Phase 2 — Backend Status API and Wiring

## Goal

Add lean backend API contracts for processing/domain/job status so future UI phases consume stable Context Engine data instead of raw LightRAG payloads.

This is the core integration phase.

## Scope

Allowed:

- Add normalized schemas.
- Add backend-only LightRAG status adapter if missing.
- Add status aggregation service that joins document/job/domain state.
- Add admin detailed routes and user-safe read-only routes.
- Add backend tests.

Not allowed:

- Building full UI surfaces.
- Exposing raw LightRAG status payloads directly to frontend.
- Adding SSE/WebSockets.
- Replacing the job system.
- Creating a second document registry.

## Backend inspection

```bash
rg -n "class .*Document|Document.*Status|ingestion-status|track_id|Job|jobs|LightRAG|pipeline_status|status_counts" app tests
rg -n "lightrag.*adapter|RemoteAdapter|DomainRegistry|DomainService|Lifecycle" app
rg -n "APIRouter|include_router" app/main.py app/api/routes
```

## Proposed modules

Use existing modules if equivalents exist.

```txt
app/schemas/processing_status.py
app/integrations/lightrag/processing_status_adapter.py
app/services/processing_status_service.py
app/api/routes/processing_status.py
```

## Proposed routes

| Route | Auth | Purpose |
|---|---|---|
| `GET /documents/{document_id}/processing-status` | authenticated, document-readable | safe single document status |
| `GET /lightrag/domains/{domain_id}/processing-status` | authenticated, domain-readable | user-safe domain indexing status |
| `GET /admin/lightrag/domains/{domain_id}/processing-status` | admin | detailed domain/runtime/pipeline status |
| `GET /admin/lightrag/domains/{domain_id}/documents/processing-status` | admin | document status table data |

## Adapter responsibilities

`LightRAGProcessingStatusAdapter` should support:

- `get_pipeline_status(domain_id)`
- `get_status_counts(domain_id)`
- `get_track_status(domain_id, track_id)` if track IDs are stored
- optionally `list_documents_status(domain_id, page, page_size)`

Adapter rules:

- Resolve domain using existing domain registry/control plane.
- Use backend HTTP client only.
- Do not expose raw response as public schema.
- Map failures to typed adapter errors.

## Aggregation service responsibilities

`ProcessingStatusService` should:

- read Context Engine document registry
- read jobs for active/recent operations
- read LightRAG domain status/manifest/lifecycle state
- enrich with LightRAG status snapshots
- return stable normalized schemas
- return stale partial status on LightRAG failure when possible

## Cache/coalescing

Start simple:

- In-memory TTL cache per domain.
- Busy TTL: 2–5 seconds.
- Idle TTL: 15–30 seconds.
- Return `stale=true` and `poll_error` if LightRAG is unreachable.

## Tests

Required backend tests:

- schema mapping test
- adapter mapping test with fake LightRAG payloads
- service aggregation test with document + job + lightrag snapshot
- user-safe route hides admin-only details
- admin route includes detailed fields
- LightRAG failure returns partial/stale status

## Validation

```bash
python -m pytest -q
```

Run frontend build too if API types/client added in same phase:

```bash
cd client
npm run lint
npm run build
```

## Human inspection gate

Inspect API responses before UI implementation.

Questions:

- Are response contracts stable and frontend-ready?
- Are raw LightRAG payloads hidden?
- Does admin/user auth separation work?
- Does failure degrade gracefully?
