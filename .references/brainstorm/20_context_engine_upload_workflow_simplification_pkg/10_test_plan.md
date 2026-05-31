# Test Plan

## Baseline tests

```bash
pytest
```

Run migrations to head:

```bash
python -m alembic -c migrations/alembic.ini upgrade head
```

Adjust command if the repo uses a different Alembic path.

## Unit tests

### Status transition tests

```text
queued document ingest -> document uploaded/indexing depending on selected policy
running parsing -> document indexing, operation running/parsing
running indexing_lightrag -> document indexing
waiting_remote -> document indexing, operation running/waiting_remote
succeeded -> document ready, operation succeeded/complete
failed -> document failed, operation failed/failed
```

### Remote status mapping tests

```text
LightRAG pending/queued -> queued/waiting
LightRAG processing/indexing -> running/indexing_lightrag
LightRAG ready/completed -> succeeded/ready
LightRAG failed/error -> failed/failed
unknown/unreachable -> keep local state, mark stale diagnostic
```

## API tests

```text
POST /admin/documents/upload returns document_id, operation_id/job_id, status_url
GET /documents/{id}/processing-status returns status/stage/message/can_retry
GET /admin/lightrag/domains/{id}/documents/processing-status returns list rows
POST /admin/documents/{id}/retry-ingestion creates new operation
GET /jobs remains admin-only diagnostic
```

## Worker tests

```text
worker marks operation running
worker updates stages in order
worker marks success ready
worker marks failure failed
busy domain requeues or waits without creating duplicate active operations
```

## Poller tests

```text
poller only checks waiting/indexing documents
poller maps remote terminal success to ready
poller maps remote terminal failure to failed
poller does not parse or reingest documents
```

## UI smoke test

```text
1. Create/start LightRAG domain.
2. Upload PDF from Documents surface.
3. Confirm row appears with Processing status.
4. Confirm status updates via processing-status only.
5. Confirm ready document can be opened/viewed.
6. Force failure or mock failed state.
7. Confirm Retry appears and calls retry-ingestion.
8. Confirm domain card only exposes Start/Stop/Delete.
```
