# Workspace Tree and Context Panel Contract

## Current Backend Workspace Tree

The backend exposes a domain-scoped workspace-tree route:

```text
GET /lightrag/domains/{domain_id}/workspace-tree
```

The service builds a tree rooted at a domain and includes readable ready documents plus document structure such as sections, pages, chunks, and assets.

## Current Frontend Tree

The frontend `WorkspaceTree` component appears to render a `SourceTreeSnapshot` from chat state and says retrieved source structure appears after the first backend chat turn.

This means the UI may not yet be using the backend workspace-tree endpoint as the source of truth.

## Recommended Contract

Use backend workspace tree for persistent corpus navigation:

```text
Domain
  → Document
      → Section
          → Page
          → Chunk
          → Asset
```

Use retrieve evidence to annotate/highlight nodes:

```text
Evidence reference_id
  → document_id
  → page_number/page_start
  → section_id/title
  → chunk_id
  → asset_ids
```

## Backend Tree Node Shape

Recommended stable node fields:

```json
{
  "id": "node-id",
  "type": "domain|document|section|page|chunk|asset",
  "label": "Display label",
  "document_id": "doc-id",
  "section_id": "section-id",
  "chunk_id": "chunk-id",
  "asset_id": "asset-id",
  "page_number": 1,
  "status": "ready|processing|failed",
  "children": []
}
```

## Context Panel Item Shape

Frontend context panel should accept a mapped evidence item:

```json
{
  "id": "E1",
  "kind": "text|table|figure",
  "title": "Document title · p. 4",
  "content": "Evidence snippet",
  "document_id": "doc-id",
  "source_path": "uploads/file.pdf",
  "chunk_id": "chunk-id",
  "reference_id": "E1",
  "page_start": 4,
  "page_end": 4,
  "section_title": "Section title",
  "score": 0.82,
  "assets": []
}
```

## Required Frontend Adapter

Add a small adapter:

```text
RetrieveResponse
  → Chat message context
  → ContextPanelItem[]
  → Evidence-highlighted workspace tree nodes
```

Suggested file:

```text
client/src/lib/retrieve-response-adapter.ts
```

or near existing chat API client code.

## Acceptance Criteria

- workspace tree fetches from backend by selected domain ID
- context panel renders backend evidence with stable citation IDs
- evidence can highlight or link to tree nodes
- empty evidence renders gracefully
- image/table assets render as compact cards when available
