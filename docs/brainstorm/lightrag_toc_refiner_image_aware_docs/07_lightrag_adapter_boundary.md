# 07 — LightRAG Adapter Boundary

## Goal

Keep LightRAG as the semantic retrieval engine without letting it own local navigation and asset storage.

## Adapter Responsibility

```python
class LightRagIngestionAdapter:
    async def ingest_chunks(
        self,
        domain_id: str,
        chunks: list[DocumentChunk],
    ) -> None:
        ...
```

```python
class LightRagQueryAdapter:
    async def query(
        self,
        domain_id: str,
        query: str,
        options: QueryOptions,
    ) -> LightRagQueryResult:
        ...
```

## Chunk Payload to LightRAG

```json
{
  "text": "Section: 4.2 Filter Replacement\nPage: 38-41\n...",
  "metadata": {
    "document_id": "doc_123",
    "section_id": "sec_004",
    "chunk_id": "chunk_004_002",
    "page_start": 38,
    "page_end": 41,
    "asset_ids": ["asset_018"]
  }
}
```

## What LightRAG Should Return

Ideally LightRAG returns:

```json
{
  "answer": "...",
  "sources": [
    {
      "chunk_id": "chunk_004_002",
      "document_id": "doc_123",
      "section_id": "sec_004",
      "score": 0.91
    }
  ]
}
```

If LightRAG cannot return all metadata directly, Context Engine should still maintain a mapping from uploaded text/chunk ids to local chunk records.

## Hard Boundary

LightRAG does not own:

```text
original uploaded files
extracted images
thumbnails
asset metadata tables
Docling manifests
PageIndex refinement logs
TUI navigation screens
Context Engine user permissions
```

## Why This Matters

This keeps the system simple:

```text
Context Engine is the control plane.
LightRAG is the retrieval engine.
```

No duplicate embeddings. No duplicate image storage. No parallel document navigation database.
