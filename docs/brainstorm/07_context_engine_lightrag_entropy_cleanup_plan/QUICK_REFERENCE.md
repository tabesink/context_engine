# Quick Reference: What to Remove vs Keep

## Remove or disable

```text
LIGHTRAG_ENABLED=false runtime mode
local semantic fallback
local hashed embedding adapter
SemanticIndexBuilder runtime usage
SemanticChunkRow runtime usage
DocumentRepository.replace_semantic_chunks runtime usage
DocumentRepository.list_semantic_chunks runtime usage
semantic_engine=self.navigation_engine wiring
silent raw upload fallback when structure ingestion fails
unknown LightRAG status → indexing fallback
unsupported answer general fallback without LLM provider
```

## Keep

```text
NavigationRetrievalEngine
local document structure
page lookup
section lookup
source chunks for grounding/navigation
assets
thumbnails
TOC refinement reports
admin upload API
job orchestration
LightRAG remote adapter
LightRAG domain management
TUI as API client
```

## Final mental model

```text
Context Engine = control plane + navigation plane
LightRAG = semantic retrieval plane
```
