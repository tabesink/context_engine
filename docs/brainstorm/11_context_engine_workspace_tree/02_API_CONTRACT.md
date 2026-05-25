# API Contract: Workspace Tree

## Endpoint

```http
GET /lightrag/domains/{domain_id}/workspace-tree
```

## Auth

Requires the same bearer-token authentication used by the rest of `context_engine`.

The route should use:

```python
user: UserRow = Depends(get_current_user)
```

## Purpose

Return a tree representing all ready documents associated with the selected LightRAG domain, expanded using Context Engine's local navigation structure.

This endpoint is intended for the future WebUI left-side workspace/document tree.

This is a native Context Engine browser contract, not the lifted Easy Deploy chat source-tree contract. The future WebUI may adapt this nested response into its existing flat `SourceTreeSnapshot` component shape, but that adapter should live at the WebUI boundary. The backend should not add port-based routes, conversation source-tree snapshots, or Easy Deploy compatibility DTOs for this feature.

## Request

### Path parameters

| Name | Type | Required | Description |
|---|---:|---:|---|
| `domain_id` | string | yes | LightRAG domain ID selected in the WebUI |

### Query parameters for first pass

None.

Optional query parameters can be added later.

## Response: success

```json
{
  "domain_id": "manuals",
  "display_name": "Manuals",
  "document_count": 2,
  "root": {
    "id": "domain:manuals",
    "kind": "domain",
    "title": "Manuals",
    "children": [
      {
        "id": "document:11111111-1111-1111-1111-111111111111",
        "kind": "document",
        "title": "Pump Manual.pdf",
        "document_id": "11111111-1111-1111-1111-111111111111",
        "status": "ready",
        "filename": "Pump Manual.pdf",
        "content_type": "application/pdf",
        "children": [
          {
            "id": "section:11111111-1111-1111-1111-111111111111:introduction",
            "kind": "section",
            "title": "Introduction",
            "document_id": "11111111-1111-1111-1111-111111111111",
            "section_id": "introduction",
            "page_start": 1,
            "page_end": 2,
            "children": [
              {
                "id": "page:11111111-1111-1111-1111-111111111111:1",
                "kind": "page",
                "title": "Page 1",
                "document_id": "11111111-1111-1111-1111-111111111111",
                "page_number": 1,
                "children": []
              }
            ]
          }
        ]
      }
    ],
    "metadata": {
      "is_healthy": true,
      "is_default": false
    }
  }
}
```

## Response: valid domain, no documents

```json
{
  "domain_id": "manuals",
  "display_name": "Manuals",
  "document_count": 0,
  "root": {
    "id": "domain:manuals",
    "kind": "domain",
    "title": "Manuals",
    "children": [],
    "metadata": {
      "is_healthy": true,
      "is_default": false
    }
  }
}
```

## Response: unknown domain

```http
404 Not Found
```

Example body:

```json
{
  "detail": "LightRAG domain 'manuals' not found"
}
```

## Response: unauthenticated

Use the same auth error behavior as the rest of the app.

Usually:

```http
401 Unauthorized
```

## Node contract

### Common node fields

| Field | Type | Applies to | Description |
|---|---|---|---|
| `id` | string | all | Stable tree node ID |
| `kind` | string | all | `domain`, `document`, `section`, `page`, `chunk`, or `asset` |
| `title` | string | all | Display title |
| `children` | array | all | Child nodes |
| `metadata` | object | all | Extra non-critical metadata |

### Optional action fields

| Field | Applies to | WebUI use |
|---|---|---|
| `document_id` | document/section/page/chunk/asset | Needed to call document APIs |
| `section_id` | section | Call `/documents/{document_id}/sections/{section_id}` |
| `page_number` | page | Call `/documents/{document_id}/pages/{page_number}` |
| `chunk_id` | chunk | Call `/documents/{document_id}/chunks/{chunk_id}` |
| `asset_id` | asset | Call `/documents/{document_id}/assets/{asset_id}` |
| `thumbnail_url` | asset | Display preview image |

## Frontend click behavior

| Node kind | Recommended WebUI behavior |
|---|---|
| `domain` | Show domain summary or collapse/expand |
| `document` | Show document summary/details |
| `section` | Fetch `/documents/{document_id}/sections/{section_id}` |
| `page` | Fetch `/documents/{document_id}/pages/{page_number}` |
| `chunk` | Fetch `/documents/{document_id}/chunks/{chunk_id}` |
| `asset` | Fetch `/documents/{document_id}/assets/{asset_id}` or thumbnail |

## Important API design notes

- The tree endpoint should return references, not full document content.
- Do not include full page text.
- Do not include full chunk text.
- Do not inline images/tables.
- Asset nodes should include URLs that let the WebUI load assets separately.
- The tree is domain-aware, not port-aware.
- The tree is built from local navigation, not from LightRAG retrieval output.
- A document with no saved local structure should still appear as a document node with `metadata.structure_available = false`.
- First-pass filtering is based on `documents.metadata.lightrag.domain_id`, with `documents.metadata.lightrag.domain` accepted only as a compatibility fallback for older metadata.
- The route should validate the domain through the same LightRAG domain service used by `/lightrag/domains`.

## Future WebUI adapter boundary

The current WebUI reference has two related but different tree concepts:

| Concept | Owner | Shape | When used |
|---|---|---|---|
| Domain workspace tree | Context Engine backend | Nested `WorkspaceTreeResponse` | Static domain/document browser |
| Chat source tree | Future WebUI/chat layer | Flat `SourceTreeSnapshot` | Per assistant turn retrieval context |

Keep the backend response stable and reference-only. If the WebUI needs a flat map, it should derive that from `root.children` without changing this endpoint.
