# Context Engine: Single Rich Navigation Implementation Package

This folder contains a coding-agent-friendly implementation package for simplifying `context_engine`.

## Goal

Use **one local navigation source of truth**:

```text
DocumentStructure
 ├── pages
 ├── sections
 ├── blocks
 ├── source_chunks
 └── assets
```

LightRAG remains the owner of semantic retrieval.

The backend becomes the owner of deterministic local navigation, page lookup, section lookup, citations, and assets.

## Main Decisions

1. Persist `DocumentPage` as part of the rich document structure.
2. Make page APIs read from `document_pages`.
3. Make structure APIs read from rich `DocumentStructure` only.
4. Replace the old page-only local navigation engine with `RichNavigationEngine`.
5. Remove optional LLM-based TOC refinement during ingestion.
6. Remove the old `parsed_documents` and `navigation_indexes` local navigation layer after migration.

## Recommended Reading Order

1. `00_index.md`
2. `01_architecture_decision.md`
3. `02_current_state_evidence.md`
4. `03_target_architecture.md`
5. `04_phase_1_add_document_pages.md`
6. `05_phase_2_repository_save_load_pages.md`
7. `06_phase_3_remove_toc_refinement.md`
8. `07_phase_4_page_and_structure_apis.md`
9. `08_phase_5_rich_navigation_engine.md`
10. `09_phase_6_remove_old_navigation_layer.md`
11. `10_testing_plan.md`
12. `11_migration_rollout.md`
13. `12_coding_agent_prompt.md`
14. `13_definition_of_done.md`
