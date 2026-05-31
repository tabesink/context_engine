# Phase 5 Prompt — Collapse Retry into Document-Based Action

Implement Phase 5 only.

Goal:

```text
Normal UI retries failed ingestion by document ID, not job ID.
```

Tasks:

```text
1. Add POST /admin/documents/{document_id}/retry-ingestion.
2. Implement DocumentRetryService.
3. Validate document is failed/retryable.
4. Create a new operation/job row.
5. Set document status through status service.
6. Enqueue worker.
7. Return document_id, operation_id/job_id, status_url.
8. Update UI retry button to call retry-ingestion.
9. Keep /jobs/{job_id}/retry as admin diagnostic compatibility only.
10. Add tests.
```
