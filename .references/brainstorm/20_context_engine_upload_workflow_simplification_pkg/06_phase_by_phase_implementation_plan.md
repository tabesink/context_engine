# Phase-by-Phase Implementation Plan

## Phase 0 — Baseline inventory and safety net

### Goal

Map the existing upload/status workflow before changing behavior.

### Commands

```bash
rg "upload|reingest|refresh-status|ingestion-status|processing-status" app tests
rg "document_ingest|JobStatus|jobs|enqueue_document_ingest" app tests
rg "status_poller|poll_lightrag|refresh_pending_lightrag" app tests
rg "metadata.*lightrag|lightrag.*status" app tests
```

### Deliverables

```text
docs/architecture/upload_status_state_ownership.md
```

### Acceptance criteria

```text
[ ] Existing tests pass.
[ ] Current upload route is identified.
[ ] Current worker task is identified.
[ ] Current poller/reconciler is identified.
[ ] Current processing-status service is identified.
[ ] No code behavior changed yet.
```

---

## Phase 1 — Lock UI polling onto processing-status

### Goal

Make `processing-status` the only normal UI polling contract.

### Backend tasks

```text
[ ] Confirm processing-status endpoints return document_id, filename, status, job/operation id, job/operation status, message, can_retry, updated_at.
[ ] Add missing operation/stage/message fields to response if not already present.
[ ] Keep ingestion-status endpoints but mark them deprecated in code comments/docs.
```

### Frontend tasks

```text
[ ] Upload flow uses POST /admin/documents/upload.
[ ] After upload, frontend polls /documents/{document_id}/processing-status or admin equivalent.
[ ] Domain document table uses /admin/lightrag/domains/{domain_id}/documents/processing-status.
[ ] Do not build new UI against ingestion-status.
[ ] Do not use /jobs as primary upload progress source.
```

### Acceptance criteria

```text
[ ] Upload UI shows status from processing-status only.
[ ] Status chip/message updates without using jobs endpoint directly.
[ ] Frontend stops polling when ready/failed/deleted.
```

---

## Phase 2 — Add operation fields to jobs table

### Goal

Make existing jobs capable of behaving like generic operations without a risky table rename.

### Add columns

```text
resource_type
resource_id
stage
message
progress_current
progress_total
started_at
finished_at
```

If these were already added by the broader control-plane simplification package, only add missing fields:

```text
stage
message
```

### Backfill

```text
if document_id is not null:
  resource_type = document
  resource_id = document_id
  stage = queued or complete based on status
```

### Code tasks

```text
[ ] Add Operation/Job compatibility model.
[ ] Add repository methods for operation stage/message updates.
[ ] Update upload path to return operation_id in addition to job_id if using compatibility period.
[ ] Keep job_id alias during transition.
```

### Acceptance criteria

```text
[ ] Upload returns document_id + operation_id/job_id + status_url.
[ ] Worker can update stage/message.
[ ] Processing-status can show stage/message.
```

---

## Phase 3 — Centralize status transitions

### Goal

Prevent route, worker, poller, and presenter from independently mutating status.

### Add or refactor service

```text
DocumentIngestionStatusService
```

Required methods:

```text
mark_queued(document_id, operation_id)
mark_running(document_id, operation_id, stage, message)
mark_waiting_remote(document_id, operation_id, message)
mark_succeeded(document_id, operation_id)
mark_failed(document_id, operation_id, error_message)
reconcile_remote_status(document_id)
```

### Update call sites

```text
[ ] Upload service uses mark_queued.
[ ] Worker uses mark_running / mark_succeeded / mark_failed / mark_waiting_remote.
[ ] Poller uses reconcile_remote_status.
[ ] Manual refresh-status route uses reconcile_remote_status.
[ ] ProcessingStatusService remains read/composition oriented.
```

### Acceptance criteria

```text
[ ] Status transition rules are not duplicated across worker/poller/routes.
[ ] documents.status and operation.status/stage remain consistent.
```

---

## Phase 4 — Make LightRAG metadata non-authoritative

### Goal

Stop treating `documents.metadata.lightrag.status` as a source of truth.

### Tasks

```text
[ ] Replace authoritative metadata status reads with operation/document status reads.
[ ] Keep metadata.lightrag.last_remote_status if needed.
[ ] Store remote IDs, domain ID, embedding fingerprint, and last_remote_check_at in metadata.
[ ] Update processing-status to map remote status through reconciler/read service.
```

### Acceptance criteria

```text
[ ] UI status does not depend on metadata.lightrag.status.
[ ] Remote LightRAG status appears only as optional diagnostic/raw payload.
```

---

## Phase 5 — Collapse retry into document-based action

### Goal

Expose one product-facing retry action.

### Add endpoint

```text
POST /admin/documents/{document_id}/retry-ingestion
```

### Behavior

```text
[ ] Validate document exists and admin can access it.
[ ] Validate current state is failed/retryable.
[ ] Create a new operation.
[ ] Reset document.status to indexing.
[ ] Return document_id, operation_id, status_url.
```

### Keep temporarily

```text
POST /admin/documents/{document_id}/reingest
POST /jobs/{job_id}/retry
```

But mark as compatibility/admin diagnostics.

### Acceptance criteria

```text
[ ] Normal UI retry uses document ID, not job ID.
[ ] Failed upload row can retry from Documents surface.
[ ] Retry creates a new operation rather than mutating old failed history destructively.
```

---

## Phase 6 — Cleanup and deprecation

### Goal

Remove or demote old status surfaces.

### Tasks

```text
[ ] Mark ingestion-status endpoints deprecated or remove after frontend migration.
[ ] Rename jobs to operations at API level, keeping DB table if desired.
[ ] Keep /jobs as compatibility/admin alias if needed.
[ ] Remove upload/status controls from domain lifecycle menu.
[ ] Keep domain lifecycle menu to Start / Stop / Delete.
```

### Acceptance criteria

```text
[ ] Product UI has one upload status path.
[ ] Admin diagnostics are clearly separate.
[ ] Worker/poller are not exposed as product concepts.
```
