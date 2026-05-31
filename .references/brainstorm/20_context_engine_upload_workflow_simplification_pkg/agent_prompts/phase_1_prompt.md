# Phase 1 Prompt — Lock UI Polling to Processing-Status

Implement Phase 1 only.

Goal:

```text
Make processing-status the only normal UI polling surface for upload/document processing.
```

Tasks:

```text
1. Inspect processing-status response schemas.
2. Ensure document status response includes document_id, filename, status, operation/job id, operation/job status, stage/message if available, can_retry, updated_at.
3. Update frontend upload flow to poll processing-status after upload.
4. Stop new frontend code from using ingestion-status.
5. Do not use /jobs as primary upload progress source.
6. Add tests or smoke checklist.
```

Do not modify DB schema in this phase unless absolutely necessary.
