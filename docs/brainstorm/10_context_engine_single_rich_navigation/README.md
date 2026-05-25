# Context Engine Entropy Reducer Package

**Repo:** `https://github.com/tabesink/context_engine.git`  
**Audience:** junior developers, coding agents, reviewers  
**Purpose:** finish the current partial cleanup and make the codebase lighter, simpler, and lower entropy.

## North Star

```text
Context Engine should be a control + retrieval orchestration backend.

It owns:
  - users/auth/admin control
  - document upload metadata
  - deterministic local navigation
  - rich document structure
  - pages/sections/chunks/assets/citations
  - retrieval API/TUI developer workflow

LightRAG owns:
  - semantic retrieval
  - embeddings
  - vector/graph retrieval
  - semantic/graph storage
```

## Critical Current Finding

The repo appears to be in a **partial migration state**:

```text
RichNavigationEngine exists.
DocumentProcessingRepository has been partially updated for pages.
But retrieval/page/structure APIs still partially use old navigation paths.
TOC refinement is still wired.
Old parsed_documents/navigation_indexes paths still exist.
```

This package prioritizes stabilization first.

## Recommended Reading Order

1. `00_current_state_summary.md`
2. `01_stabilization_first.md`
3. `02_phase_document_pages.md`
4. `03_phase_wire_rich_navigation.md`
5. `04_phase_remove_toc_refinement.md`
6. `05_phase_collapse_ingestion_jobs.md`
7. `06_phase_simplify_api_surface.md`
8. `07_phase_remove_old_navigation_stack.md`
9. `08_phase_lightrag_boundary_and_config.md`
10. `09_testing_and_migration_plan.md`
11. `10_coding_agent_prompt.md`
12. `11_junior_dev_review_checklist.md`
13. `12_definition_of_done.md`

## Important Rule

Do not start broad refactors before stabilizing the current partial migration.

Start with:

```text
DocumentPageRow
DocumentPage.metadata
DocumentProcessingRepository page save/load
Page API -> rich pages
RetrievalService -> RichNavigationEngine
Structure API -> rich-only
Remove TOC refinement
```
