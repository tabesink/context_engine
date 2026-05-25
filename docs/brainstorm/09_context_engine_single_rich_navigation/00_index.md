# 00 — Package Index

## Purpose

This documentation package breaks the implementation into small markdown files so coding agents and junior developers can work phase by phase.

## Core Principle

```text
LightRAG = semantic retrieval owner
DocumentStructure = deterministic local navigation owner
```

## Implementation Phases

| Phase | File | Outcome |
|---|---|---|
| 1 | `04_phase_1_add_document_pages.md` | Add `document_pages` table and `DocumentPageRow`. |
| 2 | `05_phase_2_repository_save_load_pages.md` | Save/load `DocumentStructure.pages`. |
| 3 | `06_phase_3_remove_toc_refinement.md` | Remove LLM-based TOC refinement. |
| 4 | `07_phase_4_page_and_structure_apis.md` | Move APIs to rich structure only. |
| 5 | `08_phase_5_rich_navigation_engine.md` | Add deterministic rich navigation retrieval. |
| 6 | `09_phase_6_remove_old_navigation_layer.md` | Remove old local navigation layer. |

## Review Gates

Before merging each phase:

```bash
pytest
ruff check .
alembic upgrade head
```

Run `mypy .` too if the repository already uses mypy.
