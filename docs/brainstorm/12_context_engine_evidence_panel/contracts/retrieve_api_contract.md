# Retrieve API Contract

## Endpoint

```text
POST /retrieve
```

Removed routes:

```text
POST /query/retrieve
```

`/query/retrieve` is not supported in the current backend. It should return 404 unless a future API decision explicitly restores it.

## Auth

Requires the existing authenticated user dependency used by backend API routes.

## Request

```json
{
  "query": "string",
  "mode": "auto",
  "document_ids": null,
  "lightrag_domain_id": null,
  "top_k": 8,
  "include_debug": false,
  "include_assets": false,
  "include_thumbnails": true,
  "max_assets": 5
}
```

## Request Fields

| Field | Type | Required | Default | Notes |
|---|---|---:|---|---|
| `query` | string | yes | none | Must be non-empty. |
| `mode` | enum | no | `auto` | `auto`, `semantic`, `navigation`, `hybrid`. |
| `document_ids` | string[] or null | no | null | Limits retrieval scope. |
| `lightrag_domain_id` | string or null | no | null | Selected LightRAG domain. |
| `top_k` | int | no | 8 | Clamp to backend schema limits. |
| `include_debug` | bool | no | false | Backend should only return debug for admin. |
| `include_assets` | bool | no | false | Include images/tables/figures if available. |
| `include_thumbnails` | bool | no | true | Include thumbnail URLs when assets are returned. |
| `max_assets` | int | no | 5 | Maximum assets returned. |

## Response

```json
{
  "query": "string",
  "mode": "hybrid",
  "evidence": [],
  "assets": [],
  "debug": null
}
```

## Response Fields

| Field | Type | Notes |
|---|---|---|
| `query` | string | Echo of request query. |
| `mode` | enum | Retrieval mode actually used by service/result. |
| `evidence` | EvidenceItem[] | Ordered by backend ranking. |
| `assets` | AssetItem[] | Optional related images/tables/figures. |
| `debug` | object or null | Only returned for admin when requested. |

## Evidence Item

```json
{
  "evidence_id": "string",
  "document_id": "string",
  "source_engine": "lightrag",
  "text": "string",
  "score": 0.87,
  "page_start": 1,
  "page_end": 2,
  "section_title": "Introduction",
  "source_path": "manual.pdf",
  "document_title": "Product Manual",
  "chunk_id": "chunk-001",
  "reference_id": "ref-001",
  "metadata": {}
}
```

## Asset Item

```json
{
  "asset_id": "string",
  "document_id": "string",
  "asset_type": "image",
  "caption": "string or null",
  "page_number": 2,
  "url": "/documents/{document_id}/assets/{asset_id}",
  "thumbnail_url": "/documents/{document_id}/assets/{asset_id}/thumbnail"
}
```

## Status Codes

| Status | Meaning |
|---:|---|
| 200 | Successful retrieval, even if evidence is empty. |
| 400 | Invalid scope, domain/document mismatch, invalid request. |
| 401 | Not authenticated. |
| 403 | Authenticated but not allowed. |
| 422 | Schema validation error. |
| 502 | LightRAG authentication/upstream/invalid response error. |
| 503 | LightRAG unavailable or timed out. |

## WebUI Rule

The WebUI must only depend on explicit top-level fields where possible.

Use `metadata` for optional display enrichment, not core rendering.

The WebUI must call `POST /retrieve` for evidence. It must not call LightRAG directly or depend on removed `/query/*` routes.
