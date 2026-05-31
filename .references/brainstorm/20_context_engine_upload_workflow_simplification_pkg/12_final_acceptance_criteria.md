# Final Acceptance Criteria

## Product workflow

```text
[ ] User/admin uploads a document from Documents surface.
[ ] UI shows one processing row.
[ ] UI polls processing-status only.
[ ] UI stops polling when ready/failed/deleted.
[ ] Failed document can retry from document row using document ID.
[ ] Ready document can be opened/viewed.
```

## Endpoint cleanup

```text
[ ] Upload route returns document_id, operation_id/job_id, and status_url.
[ ] processing-status is the normal polling surface.
[ ] ingestion-status is deprecated or unused by new UI.
[ ] /jobs is admin diagnostics only.
[ ] refresh-status is manual recovery only.
```

## State ownership

```text
[ ] documents.status owns document availability.
[ ] operation/job status owns active work.
[ ] operation/job stage owns processing phase.
[ ] metadata.lightrag does not own app status.
[ ] raw LightRAG state is mapped or shown only as diagnostics.
```

## Worker/poller

```text
[ ] Worker executes document ingest operation.
[ ] Worker updates status through one service.
[ ] Poller reconciles remote LightRAG status only.
[ ] Poller updates status through one service.
[ ] No duplicate active ingest operations per document/domain.
```

## UI separation

```text
[ ] Documents page owns upload/status/retry.
[ ] Domain lifecycle card owns Start/Stop/Delete only.
[ ] Domain lifecycle card does not expose Upload Documents.
[ ] Domain lifecycle card does not expose View Documents.
[ ] Domain lifecycle card does not expose View Logs.
```

## Low-entropy explanation

A junior developer should be able to explain the workflow as:

```text
Upload creates a document and an operation.
The worker executes the operation.
The poller only reconciles remote LightRAG completion.
The processing-status endpoint is what the UI polls.
The document status tells us whether the document is usable.
```
