# Upload And Readiness Hardening - Junior Dev Plan

## Goal

Deliver a lean backend flow for WebUI upload status and production-safe readiness checks without adding heavy orchestration.

## Why This Change Exists

- Upload endpoint already returns `{document, job_id}`, but LightRAG async indexing can outlive the local worker job.
- A status refresh helper existed but was not running automatically in deployment.
- Readiness endpoint was too shallow for WebUI/system-status UX.

## Final UX Contract (Admin Upload)

1. `POST /admin/documents/upload`
2. Poll `GET /jobs/{job_id}`
3. Poll `GET /admin/documents/{document_id}/ingestion-status`
4. Backend background poller moves document from `indexing` to `ready` or `failed`

WebUI should not use LightRAG `track_id`.

## Implementation Steps

### Step 1 - Add admin ingestion-status route

- File: `app/api/routes/admin.py`
- Add `GET /admin/documents/{document_id}/ingestion-status`.
- Route is admin-gated with `require_admin`.
- It loads document + structure and returns the same shape as user ingestion-status payload.

### Step 2 - Redact LightRAG internal IDs from ingestion payloads

- File: `app/api/routes/documents.py`
- Create a shared payload builder used by:
  - `GET /documents/{document_id}/ingestion-status`
  - `GET /admin/documents/{document_id}/ingestion-status`
- Remove `track_id` from payload under `lightrag`.
- Keep DB metadata unchanged so backend can still refresh from LightRAG.

### Step 3 - Wire recurring LightRAG status polling

- New file: `app/workers/status_poller.py`
- Loop:
  - call `poll_lightrag_statuses()`
  - sleep `LIGHTRAG_STATUS_POLL_INTERVAL_SECONDS`
- Update settings:
  - add `lightrag_status_poll_interval_seconds` in `app/core/config.py`
  - add env var to `.env.example`
- Runtime wiring:
  - add `status-poller` service in `docker-compose.yml`.

### Step 4 - Harden readiness checks

- New file: `app/services/readiness_service.py`
- Return unified model:
  - `status`: `ready | not_ready`
  - `services`:
    - `database`
    - `redis`
    - `domain_registry`
    - `lightrag`
  - each service is `healthy|unhealthy`
- Strict behavior:
  - DB must respond (`SELECT 1`)
  - Redis must respond when queue mode (`INDEX_JOBS_INLINE=false`)
  - Domain registry must be valid with default domain
  - Default domain `base_url/health` must return success
- Update route:
  - file `app/api/routes/health.py`
  - return `503` with same top-level payload when not ready.

### Step 5 - Tests

- File: `tests/test_api.py`
- Add/adjust:
  - readiness healthy path with mocked LightRAG health
  - readiness not-ready when LightRAG unhealthy
  - readiness not-ready when registry missing
  - readiness not-ready when Redis down in queue mode
  - admin ingestion-status available while document still `indexing`
  - poller refresh turns pending document from `indexing` to `ready`
  - ingestion-status payload does not expose `track_id`

## Validation Checklist

- `python3 -m compileall app tests/test_api.py`
- Run API tests with project test environment once pytest is available.
- Manual spot-check:
  - upload returns `job_id`
  - admin ingestion-status works before `ready`
  - readiness returns dependency map and 503 when default domain is down.

## Rollout Notes

- Keep `POST /admin/documents/{document_id}/refresh-status` as manual debug tool.
- Prefer WebUI polling of job + admin ingestion status endpoints.
- Do not add WebUI dependency on `track_id`.
