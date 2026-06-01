# 08 — Testing and Acceptance Criteria

## Backend Test Coverage

### Auth and Role Gating

- [ ] Anonymous user cannot access protected routes.
- [ ] Normal user cannot upload documents.
- [ ] Normal user cannot create/start/stop/delete domains.
- [ ] Admin can access admin routes.

### Document Upload

- [ ] Upload requires admin.
- [ ] Upload requires valid domain.
- [ ] Upload creates document row.
- [ ] Upload creates operation/job row.
- [ ] Upload returns `document_id`, `operation_id`, and `processing_status_url`.

### Processing Status

- [ ] `/documents/{id}/processing-status` works for owner/admin.
- [ ] `/admin/documents/{id}/processing-status` works for admin.
- [ ] Deprecated `ingestion-status` delegates to canonical status during transition.
- [ ] Status includes stable `status`, `stage`, `progress`, `message`, and `error_message`.

### Operations

- [ ] `/operations` lists document ingest operations.
- [ ] `/operations/{id}` returns operation details.
- [ ] Failed operation can be retried by admin.
- [ ] Non-admin cannot see global operations.
- [ ] Domain lifecycle actions appear as operations.

### Domain Lifecycle

- [ ] Admin can create domain.
- [ ] Admin can start domain.
- [ ] Admin can stop domain.
- [ ] Admin can delete domain.
- [ ] Non-admin cannot call lifecycle endpoints.
- [ ] Domain list includes desired metadata and observed health.

### Provider Config

- [ ] Provider diagnostics do not leak secrets.
- [ ] Missing key produces clear status.
- [ ] Local/Ollama mode is represented clearly.
- [ ] Domain creation validates required embedding config.
- [ ] Retrieval does not mutate provider defaults.

### Retrieval

- [ ] Retrieval requires authenticated user.
- [ ] Retrieval rejects invalid domain.
- [ ] Retrieval respects document/domain filters.
- [ ] Retrieval response includes evidence with source fields.

## Frontend Test / QA Coverage

### UI Smoke Tests

- [ ] Login works.
- [ ] Chat route loads.
- [ ] Domain dropdown loads healthy/default domain.
- [ ] Document upload page uses `processing-status`.
- [ ] Operations page displays global operations.
- [ ] Domain settings exposes only Start, Stop, Delete.
- [ ] Provider page shows diagnostics and missing/local indicators.

### Search-Based Checks

Run these before merging:

```bash
grep -R "ingestion-status" client/src
# should be empty or only in explicit deprecated compatibility tests/docs

grep -R "\/jobs" client/src
# should be empty unless a developer-only debug page intentionally remains

grep -R "repair\|recreate\|regenerate\|purge" client/src
# should not be visible in normal domain lifecycle UI
```

## Manual End-to-End Acceptance Script

1. Login as admin.
2. Create a domain.
3. Start the domain.
4. Upload a document into the domain.
5. Watch document status progress through stages.
6. Confirm operation appears in Operations page.
7. Ask a retrieval question in Chat.
8. Confirm evidence/source fields render.
9. Stop the domain.
10. Delete the domain.
11. Confirm normal user cannot perform admin operations.

## Final Definition of Done

```text
Frontend uses processing-status only.
Operations is the visible async/global activity layer.
Domain lifecycle UI exposes only create/start/stop/delete.
Provider config source of truth is documented and enforced.
Document upload stages are stable and understandable.
Frontend API calls are centralized in typed API clients.
No destructive DB migrations were performed without compatibility period.
```
