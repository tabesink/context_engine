# 03 — Target Architecture

## Final Local Navigation Model

```text
DocumentStructure
 ├── pages
 ├── sections
 ├── blocks
 ├── source_chunks
 └── assets
```

## Storage Target

```text
documents
 ├── document_pages
 ├── document_sections
 ├── document_blocks
 ├── document_source_chunks
 └── document_assets
```

## Ingestion Target

```text
Uploaded document
      │
      ▼
Docling/Text parser
      │
      ▼
DocumentStructure
      │
      ├── save pages
      ├── save sections
      ├── save blocks
      ├── save source chunks
      └── save assets
      │
      ▼
Send source chunks to LightRAG
```

## Query Target

```text
POST /query/retrieve
        │
        ▼
RetrievalService
        │
        ├── mode=semantic/auto ─────► LightRAGRemoteRetrievalEngine
        │
        ├── mode=navigation ────────► RichNavigationEngine
        │
        └── mode=hybrid ────────────► LightRAG + RichNavigationEngine
```

## Page API Target

```text
GET /documents/{document_id}/pages/{page_number}
        │
        ▼
DocumentProcessingRepository.get_page()
        │
        ▼
document_pages
        │
        ▼
PageResponse
```

## Structure API Target

```text
GET /documents/{document_id}/structure
        │
        ▼
DocumentProcessingRepository.get_structure()
        │
        ▼
DocumentStructure only

No fallback to navigation_indexes.
```
