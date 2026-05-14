# LightRAG HTTP Contract

This document describes the HTTP contract currently used by `context_engine` for an external LightRAG-compatible service.

The app-facing API is not the same as the upstream LightRAG API. `context_engine` exposes its own routes and hides upstream response quirks inside `app/integrations/lightrag_remote_adapter.py`.

## Configuration

LightRAG is disabled by default.

```env
LIGHTRAG_ENABLED=false
LIGHTRAG_BASE_URL=http://localhost:9621
LIGHTRAG_API_KEY=
LIGHTRAG_DOMAIN=default
LIGHTRAG_DOMAIN_MANIFEST=
LIGHTRAG_TIMEOUT_SECONDS=10
```

`LIGHTRAG_DOMAIN_MANIFEST` can point to a JSON manifest that overrides `base_url` and `api_key` per domain.

## Authentication To LightRAG

When `LIGHTRAG_API_KEY` or a domain-specific API key is configured, `context_engine` sends it to LightRAG on every upstream request:

```http
Authorization: Bearer <LIGHTRAG_API_KEY>
```

The CLI never sees this value and never calls LightRAG directly.

## Upstream Retrieval: `POST /query/data`

`LightRAGRemoteAdapter.retrieve()` calls upstream LightRAG:

```http
POST /query/data
```

Request body:

```json
{
  "query": "where are installation steps",
  "mode": "mix",
  "top_k": 8,
  "chunk_top_k": 8,
  "include_references": true,
  "include_chunk_content": true,
  "document_ids": ["doc_123"],
  "domain": "default"
}
```

`document_ids` and `domain` are omitted when not provided.

Mode mapping:

- `semantic` -> `mix`
- `hybrid` -> `mix`
- `auto` -> `mix`
- `navigation` -> local Context Engine navigation path; the adapter's `naive` mapping is not used by normal `RetrievalService` routing.

Expected upstream shape:

```json
{
  "data": {
    "chunks": [
      {
        "chunk_id": "chunk-123",
        "reference_id": "ref-123",
        "document_id": "external-doc-id",
        "content": "retrieved context",
        "score": 0.82,
        "page_start": 4,
        "page_end": 5,
        "file_path": "manual.pdf"
      }
    ],
    "references": [
      {
        "reference_id": "ref-123",
        "document_id": "external-doc-id",
        "file_path": "manual.pdf"
      }
    ]
  }
}
```

The adapter normalizes chunks and references into local `Evidence`:

```json
{
  "evidence_id": "chunk-123",
  "document_id": "stable-uuid",
  "source_engine": "lightrag",
  "text": "retrieved context",
  "score": 0.82,
  "page_start": 4,
  "page_end": 5,
  "section_title": null,
  "metadata": {
    "source_path": "manual.pdf",
    "reference_id": "ref-123",
    "external_document_id": "external-doc-id"
  }
}
```

## Upstream Upload: `POST /documents/upload`

When `LIGHTRAG_ENABLED=true`, admin upload stores a local mirror record/file and forwards the file to LightRAG:

```http
POST /documents/upload
```

Request:

- `multipart/form-data`
- file field name: `file`
- optional `domain`
- optional metadata as `metadata[key]` form fields

Expected upstream response:

```json
{
  "document_id": "external-doc-id",
  "track_id": "upload-track-id",
  "status": "success",
  "message": "Document accepted"
}
```

The adapter normalizes upload status:

- `success`, `duplicated`, `scanning_started`, `reprocessing_started` -> `indexing`
- `processed`, `ready`, `complete`, `completed` -> `ready`
- `failed`, `failure`, `error` -> `failed`

In this mode, the Context Engine upload response may include `job_id: null` because remote ingestion is owned by LightRAG rather than the local worker.

## Upstream Status: `GET /documents/track_status/{track_id}`

The adapter has a status helper for LightRAG track IDs:

```http
GET /documents/track_status/{track_id}
```

Expected upstream shape:

```json
{
  "track_id": "upload-track-id",
  "documents": [
    {
      "id": "external-doc-id",
      "status": "processed",
      "error_msg": null,
      "metadata": {}
    }
  ]
}
```

Normalized adapter response:

```json
{
  "document_id": "external-doc-id",
  "track_id": "upload-track-id",
  "status": "ready",
  "error": null,
  "metadata": {}
}
```

This helper is available in the adapter; it is not currently exposed as a separate Context Engine FastAPI route.

## App-Facing Graph Proxy Routes

Context Engine exposes authenticated graph read routes with no `/lightrag` prefix:

```http
GET /graphs?label=LABEL&max_depth=3&max_nodes=1000
GET /graph/label/list
GET /graph/label/popular?limit=300
GET /graph/label/search?q=TEXT&limit=50
```

Each route proxies the same path to the configured LightRAG service. When `LIGHTRAG_ENABLED=false`, the backend returns `400` with detail `LightRAG is disabled`.

Graph proxy responses preserve the upstream JSON shape. The current adapter does not normalize graph nodes/edges beyond HTTP error handling.

## Error Mapping

The adapter maps remote failures into typed errors:

- timeout or connection failure -> `LightRAGServiceUnavailable` -> API `503`
- invalid JSON or unexpected response shape -> `LightRAGInvalidResponse` -> API `502`
- upstream `401` or `403` -> `LightRAGAuthenticationError` -> API `502`
- other upstream HTTP error -> `LightRAGUpstreamError` -> API `502`

FastAPI route handlers and `RetrievalService` translate these into app-level HTTP errors without exposing internal LightRAG traces.
