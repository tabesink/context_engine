# Evidence Item Contract

## Purpose

An evidence item is the smallest renderable source card in the WebUI right-hand side panel.

It may come from:

- LightRAG semantic retrieval
- local rich navigation retrieval
- hybrid merge of semantic and navigation evidence

## Required Fields

| Field | Purpose |
|---|---|
| `evidence_id` | Stable card key and citation target. |
| `document_id` | Links evidence to document/page/asset APIs. |
| `source_engine` | Shows whether evidence came from `lightrag`, `navigation`, or another backend engine. |
| `text` | Snippet displayed in card. |
| `metadata` | Raw optional metadata for advanced display/debug. |

## Optional Display Fields

| Field | Purpose |
|---|---|
| `score` | Rank/confidence indicator. |
| `page_start` | Page where evidence starts. |
| `page_end` | Page where evidence ends. |
| `section_title` | Human-readable section heading. |
| `source_path` | File/source label if document title is unavailable. |
| `document_title` | Preferred human-readable source label. |
| `chunk_id` | Stable chunk reference. |
| `reference_id` | External LightRAG reference id if available. |

## Rendering Priority

For source label, use:

```text
document_title -> source_path -> document_id
```

For location, use:

```text
section_title + page range
```

For card identity, use:

```text
evidence_id
```

## Bad Evidence Item Examples

Do not return evidence with no text:

```json
{"evidence_id": "x", "text": ""}
```

Do not return raw LightRAG chunk objects directly:

```json
{"chunks": [{"content": "..."}]}
```

Do not force WebUI to parse deeply nested arbitrary metadata for core display fields.

## Good Evidence Item Example

```json
{
  "evidence_id": "lightrag:abc123",
  "document_id": "8b8d...",
  "source_engine": "lightrag",
  "text": "The warranty covers labor for 30 days after delivery.",
  "score": 0.91,
  "page_start": 3,
  "page_end": 3,
  "section_title": "Labor Warranty",
  "source_path": "Warranty Service Policy.pdf",
  "document_title": "Warranty Service Policy",
  "chunk_id": "abc123",
  "reference_id": "ref-5",
  "metadata": {
    "source": "source_chunk",
    "asset_ids": []
  }
}
```
