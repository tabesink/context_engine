# API Contracts

This document lists the stable API surfaces that should anchor frontend and integration work. Internal table names and worker details may change without changing these product contracts.

## Documents

- `GET /documents` lists authenticated-user readable documents.
- `GET /documents/{document_id}` returns document metadata.
- `GET /documents/{document_id}/processing-status` is the canonical user polling endpoint for document processing state.
- `GET /documents/{document_id}/ingestion-status` is deprecated and should only delegate to processing status during the compatibility period.

Admin document mutation routes:

- `POST /admin/documents/upload` creates a document, creates an operation, enqueues processing, and returns `document_id`, `operation_id`, and `processing_status_url`.
- `POST /admin/documents/{document_id}/retry-ingestion` creates a new retry operation and returns the same operation/status contract.
- `GET /admin/documents/{document_id}/processing-status` is the admin single-document status endpoint.

## Operations

- `GET /operations` lists admin-visible async activity.
- `GET /operations/{operation_id}` returns one operation.
- `POST /operations/{operation_id}/retry` retries supported failed operations.

Operation responses expose product-shaped fields:

```text
id
type
status
stage
progress
resource_type
resource_id
resource_label
actor_user_id
message
error_message
metadata
created_at
started_at
finished_at
updated_at
```

The `jobs` table remains the internal storage implementation. API consumers should not use a `/jobs` route for normal workflows.

## Domains

Managed LightRAG domain lifecycle routes are admin-only:

- `GET /admin/lightrag-domains`
- `POST /admin/lightrag-domains`
- `GET /admin/lightrag-domains/{domain_id}`
- `POST /admin/lightrag-domains/{domain_id}/start`
- `POST /admin/lightrag-domains/{domain_id}/stop`
- `DELETE /admin/lightrag-domains/{domain_id}`

Authenticated users may call `GET /lightrag/domains` for the safe domain list used by upload, retrieval, and graph browsing UI.

## Providers

- `GET /admin/ai-settings` returns provider profiles, defaults, and secret presence diagnostics without leaking secret values.
- Profile/default/secret mutation routes under `/admin/ai-settings` are admin-only.
- Generated `domain.env` files are deployment snapshots, not the editable provider API.

## Retrieval

- `POST /retrieve` returns evidence for the requested query and optional domain/document filters.
- `include_debug=true` may return debug fields for admins only.
- LightRAG upstream failures should surface as structured API errors rather than fallback semantic answers.
