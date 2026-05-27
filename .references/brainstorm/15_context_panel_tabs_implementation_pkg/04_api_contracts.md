# 04 — API Contracts

## Existing workspace tree endpoint

```http
GET /lightrag/domains/{domain_id}/workspace-tree?depth=<int>&include_assets=<bool>
```

Current purpose: load the deterministic source tree for a LightRAG domain.

Current node shape already supports:

```json
{
  "id": "chunk:doc_123:chunk_456",
  "kind": "chunk",
  "title": "Short text snippet...",
  "children": [],
  "document_id": "doc_123",
  "section_id": "sec_1",
  "page_start": 4,
  "page_end": 5,
  "chunk_id": "chunk_456",
  "metadata": {}
}
```

## New source context endpoint

```http
GET /lightrag/domains/{domain_id}/workspace-context?node_id=<node_id>
```

### Query params

| Name | Required | Description |
|---|---:|---|
| `node_id` | yes | Workspace-tree node ID, URL encoded by the client. |

### Example requests

```http
GET /lightrag/domains/forging-kb/workspace-context?node_id=document%3Adoc_123
GET /lightrag/domains/forging-kb/workspace-context?node_id=section%3Adoc_123%3Asec_004
GET /lightrag/domains/forging-kb/workspace-context?node_id=page%3Adoc_123%3A12
GET /lightrag/domains/forging-kb/workspace-context?node_id=chunk%3Adoc_123%3Achunk_456
GET /lightrag/domains/forging-kb/workspace-context?node_id=asset%3Adoc_123%3Atable_002
```

## Source context response

```json
{
  "node_id": "chunk:doc_123:chunk_456",
  "kind": "chunk",
  "title": "Local thinning near rib transition",
  "domain_id": "forging-kb",
  "breadcrumb": [
    { "id": "domain:forging-kb", "kind": "domain", "title": "Forging KB" },
    { "id": "document:doc_123", "kind": "document", "title": "FLCA Forging Study.pdf" },
    { "id": "section:doc_123:sec_results", "kind": "section", "title": "Results" },
    { "id": "chunk:doc_123:chunk_456", "kind": "chunk", "title": "Local thinning near rib transition" }
  ],
  "document": {
    "document_id": "doc_123",
    "title": "FLCA Forging Study.pdf",
    "filename": "FLCA Forging Study.pdf",
    "content_type": "application/pdf",
    "status": "ready",
    "source_path": ".data/uploads/FLCA Forging Study.pdf"
  },
  "section_id": "sec_results",
  "page_start": 12,
  "page_end": 12,
  "chunk_id": "chunk_456",
  "summary": "Exact source chunk from Results section, page 12.",
  "text": "Local thinning occurs near the rib transition during the final forging stage...",
  "assets": [
    {
      "asset_id": "fig_003",
      "document_id": "doc_123",
      "asset_type": "figure",
      "title": "Figure 3",
      "caption": "Effective strain distribution",
      "page_number": 12,
      "section_id": "sec_results",
      "url": "/documents/doc_123/assets/fig_003",
      "thumbnail_url": "/documents/doc_123/assets/fig_003/thumbnail",
      "mime_type": "image/png",
      "metadata": {}
    }
  ],
  "metadata": {
    "source": "document_processing_structure"
  }
}
```

## Error responses

### Invalid node ID

```http
400 Bad Request
```

```json
{ "detail": "Invalid workspace node id" }
```

### Missing source context

```http
404 Not Found
```

```json
{ "detail": "Workspace source context not found" }
```

### Domain unavailable

Use existing `LightRAGDomainRegistryError` handling and existing domain HTTP exception mapper.

## Retrieval response addition

Add optional field to `EvidenceResponse`:

```json
{
  "evidence_id": "ev_1",
  "document_id": "doc_123",
  "source_engine": "lightrag",
  "text": "...",
  "chunk_id": "chunk_456",
  "reference_id": "3",
  "workspace_node_id": "chunk:doc_123:chunk_456",
  "metadata": {}
}
```

Frontend can then open the exact source navigator:

```ts
if (item.workspace_node_id) {
  await fetchWorkspaceSourceContext(activeDomainId, item.workspace_node_id);
}
```

## TypeScript API client

Add:

```ts
export async function fetchWorkspaceSourceContext(
  domainId: string,
  nodeId: string,
): Promise<WorkspaceSourceContext> {
  const params = new URLSearchParams({ node_id: nodeId });
  return apiRequest(
    `/lightrag/domains/${encodeURIComponent(domainId)}/workspace-context?${params.toString()}`,
  );
}
```

## Node ID contract

Current node ID examples:

```text
domain:{domain_id}
document:{document_id}
section:{document_id}:{section_id}
page:{document_id}:{page_number}
chunk:{document_id}:{chunk_id}
asset:{document_id}:{asset_id}
```

Rules:

- Node IDs are opaque to most frontend components.
- Only the backend source-context service should parse node IDs.
- Frontend may infer `workspace_node_id` for retrieval evidence only as a fallback.
- Long-term, if IDs may include colons, introduce URL-safe encoded node IDs.
