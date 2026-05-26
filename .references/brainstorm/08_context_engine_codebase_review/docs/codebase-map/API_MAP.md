# API Map

## API Design Summary

The backend should expose a small, clear API surface:

```text
/auth/*
/documents/*
/admin/documents/*
/retrieve
/lightrag/*
/admin/lightrag/*
/workspace-tree/*
/jobs/*
/health/*
```

The most important design choice is to keep `/retrieve` as the canonical retrieval/evidence endpoint.

Avoid adding duplicate query endpoints unless there is a distinct, well-documented product need.

## Authentication APIs

Expected owner:

```text
app/api/routes/auth.py
```

Typical responsibilities:

- login
- issue bearer token
- identify current user
- support admin/user role checks through dependencies

Important architecture rule:

Auth route should not contain document, retrieval, or LightRAG logic.

## Health APIs

Expected owner:

```text
app/api/routes/health.py
```

Typical endpoints:

```text
GET /health
GET /health/readiness
```

Typical checks:

- API process alive
- database reachable
- Redis reachable
- LightRAG availability where relevant
- worker/status-poller assumptions where relevant

## Documents APIs

Expected owner:

```text
app/api/routes/documents.py
```

Likely user-readable operations:

```text
GET /documents
GET /documents/{document_id}
GET /documents/{document_id}/structure
GET /documents/{document_id}/pages
GET /documents/{document_id}/sections
GET /documents/{document_id}/chunks
GET /documents/{document_id}/assets
GET /documents/{document_id}/thumbnail
```

Responsibilities:

- expose document metadata
- expose ready document structure
- expose page/section/chunk/asset information
- enforce authenticated read access

Important rule:

Document read APIs should use `DocumentAccessPolicy` or equivalent.

## Admin Document APIs

Expected owner:

```text
app/api/routes/admin.py
```

Likely admin-only operations:

```text
POST /admin/documents/upload
POST /admin/documents/{document_id}/reingest
DELETE /admin/documents/{document_id}
```

Responsibilities:

- upload files
- create processing jobs
- reingest documents
- archive/delete documents
- enforce admin-only write access

Important rule:

Do not allow regular authenticated users to modify corpus state.

## Retrieval API

Expected owner:

```text
app/api/routes/retrieve.py
```

Canonical endpoint:

```text
POST /retrieve
```

Expected request concepts:

```json
{
  "query": "plain-language question",
  "lightrag_domain_id": "optional-selected-domain",
  "document_ids": ["optional-document-filter"],
  "mode": "optional-retrieval-mode",
  "top_k": 10,
  "include_assets": true
}
```

Expected response concepts:

```json
{
  "answer": "optional, if answer composition is enabled",
  "evidence": [
    {
      "reference_id": "stable citation id",
      "document_id": "document id",
      "document_title": "title",
      "source_path": "path or filename",
      "chunk_id": "chunk id",
      "page_number": 1,
      "score": 0.87,
      "text": "evidence text",
      "metadata": {},
      "assets": []
    }
  ],
  "metadata": {
    "retrieval_mode": "hybrid",
    "lightrag_domain_id": "domain"
  }
}
```

Important design rule:

`/retrieve` should return evidence in a frontend-stable shape. The frontend should not parse deeply nested LightRAG-specific metadata for core display fields.

## LightRAG Domain APIs

Expected owner:

```text
app/api/routes/lightrag.py
```

User-readable operations:

```text
GET /lightrag/domains
```

Responsibilities:

- list available domains
- expose safe domain metadata
- avoid exposing secrets or container internals

## Admin LightRAG Lifecycle APIs

Expected owner:

```text
app/api/routes/lightrag_admin.py
```

Admin-only operations may include:

```text
POST /admin/lightrag/domains
POST /admin/lightrag/domains/{domain_id}/start
POST /admin/lightrag/domains/{domain_id}/stop
POST /admin/lightrag/domains/{domain_id}/recreate
POST /admin/lightrag/domains/{domain_id}/regenerate
DELETE /admin/lightrag/domains/{domain_id}
```

Responsibilities:

- manage domain lifecycle
- manage deployment metadata
- manage container lifecycle where applicable
- update domain registry/manifest
- protect all writes with admin auth

## Workspace Tree APIs

Expected owner:

```text
app/api/routes/workspace_tree.py
```

Likely endpoint:

```text
GET /workspace-tree
```

or domain-scoped:

```text
GET /workspace-tree?lightrag_domain_id={domain_id}
```

Responsibilities:

- expose a tree suitable for frontend navigation
- group documents by selected domain
- include pages/sections/assets if appropriate
- avoid returning excessive content by default

## Jobs APIs

Expected owner:

```text
app/api/routes/jobs.py
```

Likely operations:

```text
GET /jobs
GET /jobs/{job_id}
```

Responsibilities:

- expose indexing/upload job state
- show processing errors
- help debug ingestion/reingestion workflows

## API Rules for Future Work

1. Do not create duplicate query endpoints.
2. Keep `/retrieve` as the canonical evidence API.
3. Keep write operations under admin routes.
4. Keep LightRAG internals hidden behind backend API contracts.
5. Keep response fields stable for frontend integration.
6. Use explicit top-level evidence fields for common display needs:
   - `source_path`
   - `document_title`
   - `chunk_id`
   - `reference_id`
   - `page_number`
   - `assets`
