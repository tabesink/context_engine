# Coding Agent Prompt

Use this prompt to recreate LightRAG-style status reporting in another codebase.

```md
You are a senior full-stack coding agent.

Your task is to recreate the LightRAG-style document upload and ingestion status-reporting system.

Read this documentation package first:

docs/status-reporting-recreation/

Goal:

Implement a backend + frontend status system where:

- upload returns a `track_id` immediately
- per-document processing status is durable
- global pipeline progress is visible
- users can see upload transfer progress separately from background processing progress
- users can filter document list by status
- users can open a pipeline dialog with live job messages
- users can cancel an active pipeline where supported
- frontend polling is efficient and does not flood the backend

Required backend APIs:

- POST /documents/upload
- GET /documents/track_status/{track_id}
- GET /documents/pipeline_status
- POST /documents/paginated
- GET /documents/status_counts
- POST /documents/cancel_pipeline
- GET /health with pipeline_active fields

Required frontend components:

- DocumentManager
- UploadDocumentsDialog
- PipelineStatusDialog
- DocumentStatusDetailsDialog
- status filter badges
- backend health store

Implementation rules:

- Do not block upload until ingestion finishes.
- Do not conflate upload progress with processing progress.
- Store durable document status separately from live pipeline progress.
- Use `track_id` for per-upload tracking.
- Use `pipeline_status` for global job progress.
- Do not poll every endpoint all the time.
- Poll `/pipeline_status` only when the dialog is open.
- Poll document table faster only while pipeline is active.
- Dedupe identical in-flight document-table requests.
- Surface async ingestion failures in document rows.
- Add tests for backend state transitions and frontend polling behavior.

Start with the task list in `CONCRETE_CODING_TASKS.md`.

Definition of done:

- A user can upload a file and immediately see that work was accepted.
- A user can watch document status transition to processed/failed.
- A user can open a live pipeline status dialog.
- A user can see status counts and filter documents.
- The frontend does not spam backend requests.
- Tests cover track status, pipeline status, document table polling, upload handling, and cancellation.
```
