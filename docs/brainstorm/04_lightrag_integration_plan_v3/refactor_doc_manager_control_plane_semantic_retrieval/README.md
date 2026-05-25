# Context Engine — LightRAG-Only Semantic Retrieval Implementation Package

This package documents the selected architecture change:

> Context Engine keeps local document metadata, optional parsed pages, and navigation indexes. LightRAG is always enabled and owns all semantic retrieval, chunking, embeddings, vector search, and graph retrieval. There is no local semantic fallback mode.

## Files

1. `00_IMPLEMENTATION_PLAN.md` — full senior-engineer implementation plan.
2. `01_CODING_AGENT_PROMPT.md` — ready-to-paste coding-agent prompt.
3. `02_MIGRATION_AND_TEST_CHECKLIST.md` — database migration, runtime validation, and test checklist.

## Key answer

Dropping `semantic_chunks` in a later migration does **not** mean saving LightRAG embeddings in Context Engine PostgreSQL. It means removing the old local fallback table after the code no longer writes or reads local embeddings. LightRAG embeddings should remain in LightRAG-managed storage only.
