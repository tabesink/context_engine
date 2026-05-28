# Context Engine + LightRAG Document Processing Status Review — Findings

Generated: 2026-05-28

Repos reviewed through GitHub web/raw access:

- Context Engine: `https://github.com/tabesink/context_engine.git`
- LightRAG: `https://github.com/HKUDS/LightRAG.git`

The container could not clone GitHub directly because DNS resolution for `github.com` failed. Findings are based on current GitHub-visible source files and raw file inspection.

---

## 1. Executive Finding

The leanest integration is **not** to copy LightRAG WebUI status behavior into the Context Engine frontend. Context Engine should remain the single API/auth boundary and should expose a **normalized Processing Status contract** that aggregates:

1. Context Engine document registry state.
2. Context Engine job state.
3. LightRAG domain lifecycle state.
4. Backend-only LightRAG processing snapshots from `track_status`, `pipeline_status`, `status_counts`, and optionally `paginated` document status.

This keeps LightRAG behind the backend, avoids frontend coupling to raw LightRAG payloads, and works for concurrent users by allowing backend caching/coalescing.

---

## 2. LightRAG Status API Surface

LightRAG has two useful status layers:

1. **Track-level status** for a specific upload/text operation.
2. **Domain/pipeline-level status** for global processing state and counts.

| LightRAG Endpoint | Method | Purpose | Key Response Fields | Context Engine Use |
|---|---:|---|---|---|
| `/documents/upload` | POST | Upload file and enqueue async processing. | `status`, `message`, `track_id` | Already used indirectly through Context Engine adapter for file upload paths or replaced by chunk-ingest flow. Keep backend-only. |
| `/documents/text` | POST | Insert one text item and enqueue async processing. | `status`, `message`, `track_id` | Do not expose to frontend directly. Useful only through adapter fallback. |
| `/documents/texts` | POST | Insert multiple text items and enqueue async processing. | `status`, `message`, `track_id` | Context Engine currently falls back to this when `/documents/ingest_chunks` is missing. |
| `/documents/track_status/{track_id}` | GET | Poll status of documents related to one upload/insert track. | `track_id`, `documents`, `total_count`, `status_summary` | Already wrapped as `LightRAGRemoteAdapter.document_status(track_id)`. Extend mapper instead of exposing raw response. |
| `/documents/pipeline_status` | GET | Poll global pipeline state. | `busy`, `job_name`, `job_start`, `docs`, `batchs`, `cur_batch`, `latest_message`, `history_messages`, `request_pending`, `update_status` | Add backend-only adapter method. Use for domain banner and admin active-operation row. |
| `/documents/paginated` | POST | List remote LightRAG document rows with status counts. | `documents`, `pagination`, `status_counts` | Optional; useful for admin domain document table only. Use sparingly because Context Engine already has a document registry. |
| `/documents/status_counts` | GET | Return counts by status. | `status_counts` | Add backend-only adapter method. Use for compact counters. |
| `/documents/scan` | POST | Scan input folder / reprocess pending files. | status and `track_id` for scan | Future admin action only. Do not implement first unless needed. |
| `/documents/reprocess_failed` | POST | Reprocess failed documents. | status and message | Future admin retry-all action. Context Engine currently has job retry/reingest; prefer existing app action first. |
| `/documents/cancel_pipeline` | POST | Request pipeline cancellation. | cancellation status and message | Future admin-only destructive action. Not needed for first status display. |
| `/health` | GET | Health and operational state. | includes pipeline busy/scanning/destructive status per docs | Useful fallback if `pipeline_status` fails, but not a replacement for status contract. |

Important LightRAG behavior:

- Upload/text endpoints return a `track_id` for async monitoring.
- `/documents/track_status/{track_id}` returns document processing status, metadata, errors, and timestamps.
- `/health` includes pipeline busy/scanning/destructive status.
- LightRAG env comments state that `/documents/paginated` is frequently polled at a 5–30s interval and `/documents/pipeline_status` can be polled every 2s by the LightRAG client.

---

## 3. Context Engine Current Status Surfaces

| Context Engine Surface | File | Current Behavior | Gap |
|---|---|---|---|
| Admin upload | `app/api/routes/admin.py` | `POST /admin/documents/upload` calls `DocumentService.upload`, creates document row and ingest job. | Upload response has document and `job_id`, but no domain-level processing snapshot. |
| User document status | `app/api/routes/documents.py` | `GET /documents/{document_id}/ingestion-status` returns document status, LightRAG metadata with `track_id` stripped, and structure booleans. | Good privacy posture; should be retained and possibly renamed/add `processing-status` alias. |
| Admin document status | `app/api/routes/admin.py` | `GET /admin/documents/{document_id}/ingestion-status` returns same helper; admin can also call `POST /admin/documents/{document_id}/refresh-status`. | Refresh is per-document only; no domain batch aggregation. |
| Jobs | `app/api/routes/jobs.py` | Admin-only list/get/retry for jobs. Retry only supports document ingest jobs. | No user-safe domain status. No joined status with LightRAG pipeline. |
| Job service | `app/services/job_service.py` | Creates `document_ingest` jobs and queues RQ or inline processing. | No domain-level aggregation/counters. |
| Worker tasks | `app/workers/tasks.py` | Runs document ingest jobs and has `poll_lightrag_statuses()`. | Polling is document-oriented, not domain snapshot-oriented. |
| LightRAG adapter | `app/integrations/lightrag_remote_adapter.py` | Supports retrieval, upload, chunk ingestion, and `document_status(track_id)`. | Missing explicit `pipeline_status`, `status_counts`, and `paginated_documents` wrappers. |
| Ingestion service | `app/services/lightrag_ingestion_service.py` | Builds structure, ingests chunks, stores track ID, applies remote status, locks domain during ingest. | Good ingestion flow; status reporting should build on its metadata instead of bypassing it. |
| Domain lifecycle | `app/api/routes/lightrag_admin.py` | Admin CRUD/up/down/recreate/repair/regenerate/archive/purge; user domain list route. | No `/processing-status` route for a domain. |
| Frontend domain store | `client/src/stores/lightrag-domain-store.ts` | Loads `/lightrag/domains` and stores selected domain. | No processing-status polling. |
| Frontend chat shell | `client/src/components/chat/LightRagChatShell.tsx` | Loads source tree, source context, retrieval context. | Status polling should not be mixed into retrieval/right-panel logic. |
| Frontend API base | `client/src/lib/api/client.ts` | All frontend requests use Context Engine API base and bearer token. | This is the correct boundary; add status client here, not direct LightRAG calls. |

---

## 4. Architectural Gaps

### G1 — No normalized domain-level processing snapshot

Current status is fragmented:

- document row status
- job row status
- LightRAG track status in metadata
- LightRAG lifecycle status
- possible remote pipeline status

There is no single backend response that can answer:

> “Is this domain currently indexing, what documents are active/failed/ready, what should admins see, and what should normal users see?”

### G2 — Existing `track_id` privacy rule is good and should stay

`ingestion_status_response()` removes `track_id` from the public LightRAG payload. This is the right pattern. Keep `track_id` backend-side and correlate through Context Engine document/job IDs.

### G3 — `LightRAGRemoteAdapter` is the right place for raw remote calls

Do not create a second HTTP client for LightRAG. Add small methods to the existing adapter:

- `pipeline_status()`
- `status_counts()`
- `paginated_documents(...)` only if needed

Then map raw responses in a service/schema layer.

### G4 — Polling must be backend-coalesced

LightRAG WebUI’s native polling cadence is too aggressive if every Context Engine user independently polls LightRAG. Context Engine should use a short backend TTL cache per domain:

- 2–5 seconds when busy
- 15–30 seconds when idle
- error backoff when LightRAG is unreachable

### G5 — UI status should be separate from evidence/source rendering

Do not add status logic to:

- retrieval adapter
- `SidePanel`
- `AssetCards`
- Source Navigator except a small passive document badge

Put status in:

- Admin Settings → LightRAG lifecycle route
- Admin Documents/upload table
- user-safe domain selector/workspace tree indicator

---

## 5. Recommended Integration Option

Use **Backend Status Aggregator + Existing Adapter Extension**.

Why:

- smallest change set
- preserves one API/auth boundary
- uses current document/job/domain tables
- avoids direct frontend LightRAG calls
- avoids duplicating status storage
- supports concurrent users through backend TTL caching
- allows admin and regular user projections from the same normalized internal snapshot

Rejected options:

| Option | Why Not First |
|---|---|
| Thin LightRAG proxy | Leaks LightRAG contract and auth model into frontend. Duplicates status concepts. |
| Full SSE/WebSocket | More moving parts; polling is enough for 5–10 users. |
| Store every LightRAG history message | Bloat; raw history can contain noisy/internal provider messages. Keep small event tail only. |
| New standalone status microservice | Overkill; Context Engine already owns jobs/documents/domains. |

---

## 6. Target Contract Summary

### User-safe domain status

```json
{
  "domain_id": "engineering",
  "state": "busy",
  "is_busy": true,
  "is_stale": false,
  "updated_at": "2026-05-28T12:00:00Z",
  "counts": {
    "queued": 1,
    "indexing": 2,
    "ready": 24,
    "failed": 1,
    "deleted": 0,
    "unknown": 0
  },
  "active": {
    "label": "Indexing documents",
    "current": 1,
    "total": 3,
    "message": "Indexing files"
  }
}
```

### Admin domain status

Adds:

```json
{
  "light_rag": {
    "reachable": true,
    "pipeline_busy": true,
    "job_name": "indexing files",
    "job_start": "2026-05-28T12:00:00Z",
    "latest_message": "...",
    "history_tail": ["..."],
    "update_status": {}
  },
  "documents": [
    {
      "document_id": "...",
      "filename": "manual.pdf",
      "status": "indexing",
      "job_id": "...",
      "job_status": "running",
      "lightrag_status": "indexing",
      "message": "...",
      "can_retry": false,
      "updated_at": "..."
    }
  ],
  "errors": []
}
```

Do not expose `track_id` in either response unless a future explicit admin-debug endpoint is added.

---

## 7. Implementation Priority

1. Extend adapter with LightRAG status methods.
2. Add normalized processing status schemas.
3. Add `ProcessingStatusService` that joins Context Engine + LightRAG status.
4. Add domain/document status routes.
5. Add frontend API client and polling hook/store.
6. Add admin domain lifecycle UI status card.
7. Add document table status chips.
8. Add user-safe domain selector indicator.

