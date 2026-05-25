# 09 — API Contracts

Keep APIs small and explicit.

## Upload

```http
POST /documents/upload
```

Request:

```json
{
  "domain_id": "manuals",
  "target_engine": "lightrag",
  "enable_toc_refinement": "auto"
}
```

Allowed `enable_toc_refinement` values:

```text
auto
always
never
```

## Query

```http
POST /domains/{domain_id}/query
```

Request:

```json
{
  "query": "Show me the wiring diagram for the controller.",
  "include_assets": true,
  "include_thumbnails": true,
  "max_assets": 5
}
```

Response:

```json
{
  "answer": "...",
  "sources": [],
  "assets": []
}
```

## Document Structure

```http
GET /documents/{document_id}/structure
```

Returns section tree without full block text by default.

Optional:

```http
GET /documents/{document_id}/structure?include_blocks=true&include_assets=true
```

## Section Detail

```http
GET /documents/{document_id}/sections/{section_id}
```

Returns:

```text
section metadata
page range
child sections
linked chunks
linked assets
```

## Chunk Detail

```http
GET /documents/{document_id}/chunks/{chunk_id}
```

Returns:

```text
chunk text
page range
section path
block ids
asset ids
LightRAG ingestion metadata
```

## Asset APIs

```http
GET /documents/{document_id}/assets/{asset_id}
GET /documents/{document_id}/assets/{asset_id}/thumbnail
```

These should stream files from local storage.

## Debug APIs

```http
GET /documents/{document_id}/ingestion-status
GET /documents/{document_id}/structure-quality
GET /documents/{document_id}/toc-refinement-report
GET /documents/{document_id}/chunks
GET /documents/{document_id}/assets
```

## Admin-only Actions

```http
POST /documents/{document_id}/rebuild-structure
POST /documents/{document_id}/reingest-lightrag
DELETE /documents/{document_id}
```

`rebuild-structure` request:

```json
{
  "enable_toc_refinement": "always",
  "preserve_assets": true
}
```
