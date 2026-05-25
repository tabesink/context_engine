# Docling + PageIndex TOC Refiner + LightRAG: Lightweight Implementation Package

This package describes a lightweight document ingestion and retrieval architecture for `context_engine` and the custom LightRAG deployment.

## Final Architecture

```text
Docling parser of record
    -> canonical DocumentStructure
    -> image/table/figure asset extraction
    -> optional PageIndex-style LLM TOC refiner
    -> section/block/chunk mapping
    -> LightRAG text ingestion with asset references
    -> retrieval response with answer + sources + images
```

## Key Decisions

1. **Docling is the parser of record.**
2. **PageIndex-style LLM TOC indexing is valuable, but only as a conditional refiner.**
3. **Context Engine owns document structure, asset files, asset metadata, navigation, and debug APIs.**
4. **LightRAG owns semantic retrieval, embeddings, and KG retrieval.**
5. **Images detected by Docling are stored once in Context Engine storage.**
6. **Chunks sent to LightRAG include only lightweight `asset_ids`, not binary image data.**
7. **During retrieval, Context Engine resolves `asset_ids` and returns relevant image URLs/thumbnails to the user.**

## Recommended Reading Order

1. `01_architecture_decision_record.md`
2. `02_user_capabilities.md`
3. `03_canonical_models.md`
4. `04_ingestion_pipeline.md`
5. `05_pageindex_toc_llm_refiner.md`
6. `06_docling_asset_extraction.md`
7. `07_lightrag_adapter_boundary.md`
8. `08_retrieval_with_images.md`
9. `09_api_contracts.md`
10. `10_storage_database_filesystem.md`
11. `11_tui_debug_screens.md`
12. `12_testing_strategy.md`
13. `13_incremental_implementation_plan.md`
14. `14_coding_agent_prompt.md`

## Implementation Goal

Build a system that lets users ask:

```text
What does this manual say?
Where does it say it?
Which section/page/table/figure supports it?
Show me the related image or diagram.
Show me the retrieval path and source chunks.
```

The system should remain small, explicit, and junior-developer friendly.
