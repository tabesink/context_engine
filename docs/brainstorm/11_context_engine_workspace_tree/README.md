# Context Engine Workspace Tree Implementation Package

This package is for a junior developer or coding agent implementing a native `workspace-tree` endpoint in `context_engine` before wiring in the lifted WebUI.

## Goal

Add a backend API that lets the WebUI display a domain-aware workspace tree:

```text
Selected LightRAG Domain
  -> all ready documents uploaded/indexed into that domain
     -> each document's local navigation structure
        -> sections
           -> pages
              -> chunks/assets
```

## Recommended first endpoint

```http
GET /lightrag/domains/{domain_id}/workspace-tree
```

## Files in this package

| File | Purpose |
|---|---|
| `01_IMPLEMENTATION_PLAN.md` | Main step-by-step implementation plan |
| `02_API_CONTRACT.md` | Request/response contract and DTOs |
| `03_TDD_TEST_PLAN.md` | Tests to write before/while implementing |
| `04_CODING_AGENT_PROMPT.md` | Copy/paste prompt for a coding agent |
| `05_REVIEW_CHECKLIST.md` | Final review checklist before WebUI wiring |

## High-level rule

Do not copy the Easy Deploy `source_tree_snapshots` model into `context_engine` for this feature.

The workspace tree should be built from `context_engine`'s existing local navigation tables and document metadata.
