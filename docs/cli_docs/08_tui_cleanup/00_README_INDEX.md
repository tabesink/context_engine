# Context Engine TUI Cleanup + LightRAG Domain Integration Plan

## Purpose

This package rewrites the terminal UI plan around the current post-login menu problem:

```text
Documents
Retrieval
LightRAG Graphs
Admin Documents
Jobs
Observability
Health / Readiness
Backend Gaps
Logout
Quit
LightRAG Domains
Create LightRAG Domain
Start LightRAG Domain
Stop LightRAG Domain
Recreate LightRAG Domain
Remove LightRAG Domain
```

The current menu is functional but too flat. LightRAG domain CRUD is repeated at the root level and should be moved inside a single `LightRAG Domains` screen. `LightRAG Graphs` should be renamed to `Graphs`. `Admin Documents` should not feel like a duplicate of `Documents`.

## Final UI Direction

The root menu should become:

```text
CONTEXT ENGINE

Backend: http://127.0.0.1:8010
Session: admin@example.com

> Documents
  Retrieval
  Graphs
  LightRAG Domains
  Jobs
  Observability
  Health / Readiness
  Backend Gaps
  Logout
  Quit
```

Admin-only actions stay available, but they move into the relevant domain screen:

```text
Documents
  ├── Browse Documents
  └── Admin Actions
        ├── Upload Document
        ├── List All Documents
        ├── Index / Reindex
        └── Delete Document

LightRAG Domains
  ├── List Domains
  ├── Create Domain
  ├── Start Domain
  ├── Stop Domain
  ├── Recreate Domain
  ├── Regenerate Domain Files
  ├── Archive Remove
  └── Permanent Delete
```

## Package Contents

| File | Purpose |
|---|---|
| `01_decisions_and_rationale.md` | Explains the menu simplification and why the old layout felt redundant. |
| `02_target_menu_and_screen_flows.md` | Final post-login menu and nested screen flows. |
| `03_documents_vs_admin_documents.md` | Explains the difference and the recommended role-aware Documents screen. |
| `04_lightrag_domains_screen_plan.md` | Detailed LightRAG Domains screen design and CRUD flow. |
| `05_graphs_rename_and_api_mapping.md` | Rename LightRAG Graphs to Graphs while keeping backend routes intact. |
| `06_tdd_implementation_plan.md` | Implementation slices and tests. |
| `07_coding_agent_prompt.md` | Ready-to-use prompt for a coding agent. |
| `context_engine_tui_lightrag_menu_cleanup_combined.md` | Combined report. |

## Implementation Rule

Do not change backend behavior just to clean up the TUI labels. First reorganize the terminal UI around the existing API contract. Only merge backend routes later if tests show the behavior is redundant.
