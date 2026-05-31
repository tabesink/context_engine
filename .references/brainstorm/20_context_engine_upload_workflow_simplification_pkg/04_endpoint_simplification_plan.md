# Endpoint Simplification Plan

## Primary UI endpoints

Use these for normal product UI.

```text
POST /admin/documents/upload
GET  /documents/{document_id}/processing-status
GET  /admin/documents/{document_id}/processing-status
GET  /admin/lightrag/domains/{domain_id}/documents/processing-status
GET  /admin/lightrag/domains/{domain_id}/processing-status
```

## Admin diagnostics only

```text
GET /jobs
GET /jobs/{job_id}
```

Later, add aliases:

```text
GET /operations
GET /operations/{operation_id}
```

## Manual recovery only

```text
POST /admin/documents/{document_id}/refresh-status
```

This should not be a normal user-facing workflow button.

## Legacy / deprecate from UI

Do not build new UI against:

```text
GET /documents/{document_id}/ingestion-status
GET /admin/documents/{document_id}/ingestion-status
```

Keep temporarily for compatibility, then remove or document as deprecated.

## Product-facing retry

Target one endpoint:

```text
POST /admin/documents/{document_id}/retry-ingestion
```

This endpoint should:

```text
1. Validate admin permissions.
2. Validate document exists.
3. Validate document is failed or retryable.
4. Create a new operation.
5. Set document.status = indexing.
6. Return document_id + operation_id + status_url.
```

## Job-based retry

Keep this only for admin diagnostics during transition:

```text
POST /jobs/{job_id}/retry
```

Do not require normal UI to know failed job IDs.
