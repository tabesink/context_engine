# 7. Coding Agent Prompt

Copy this prompt into your coding agent.

```markdown
# Task: Clean Up Context Engine TUI Menu and Nest LightRAG Domain CRUD

You are a senior software engineer. Make the terminal UI cleaner and lower entropy while preserving the existing backend API contract.

## Current Problem

After login, the TUI root menu currently shows:

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

This is too flat and redundant.

## Required New Root Menu

Change the root menu to capability areas only:

```text
Documents
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

For non-admin users, hide admin-only areas where the current TUI role model supports that.

## Required Changes

### 1. Move LightRAG domain CRUD inside LightRAG Domains

Remove these from root:

```text
Create LightRAG Domain
Start LightRAG Domain
Stop LightRAG Domain
Recreate LightRAG Domain
Remove LightRAG Domain
```

Add them inside the `LightRAG Domains` screen:

```text
LightRAG Domains
  ├── List Domains
  ├── Create Domain
  ├── Show Domain Detail
  ├── Start Domain
  ├── Stop Domain
  ├── Recreate Domain
  ├── Regenerate Domain Files
  ├── Archive Remove Domain
  └── Permanent Delete Domain
```

Use existing backend routes:

```text
GET    /admin/lightrag/domains
POST   /admin/lightrag/domains
GET    /admin/lightrag/domains/{domain_id}
POST   /admin/lightrag/domains/{domain_id}/up
POST   /admin/lightrag/domains/{domain_id}/down
POST   /admin/lightrag/domains/{domain_id}/recreate
POST   /admin/lightrag/domains/{domain_id}/regenerate
DELETE /admin/lightrag/domains/{domain_id}
DELETE /admin/lightrag/domains/{domain_id}?permanent=true
```

Do not call Docker from TUI. TUI calls `cli/services/lightrag_domains.py`, which calls backend API through `ApiClient`.

### 2. Rename LightRAG Graphs to Graphs

Change only the TUI label:

```text
LightRAG Graphs -> Graphs
```

Do not rename backend routes in this task.

Keep using:

```text
GET /graphs
GET /graph/label/list
GET /graph/label/popular
GET /graph/label/search
```

### 3. Fold Admin Documents into Documents

Remove top-level:

```text
Admin Documents
```

Inside `Documents`, add admin-only actions:

```text
Documents
  ├── Browse Ready Documents
  ├── View Document Detail
  ├── View Structure / Outline
  ├── View Page
  └── Admin Actions
        ├── Upload Document
        ├── List All Documents
        ├── Reingest / Refresh Status Document
        └── Delete Document
```

Keep backend routes unchanged:

```text
GET /documents
GET /documents/{id}
GET /documents/{id}/structure
GET /documents/{id}/pages/{page}
POST /admin/documents/upload
GET /admin/documents
POST /admin/documents/{id}/reingest
POST /admin/documents/{id}/refresh-status
DELETE /admin/documents/{id}
```

This is UI consolidation only, not a backend route merge.

## Architectural Rules

- `context-engine` and `context-tui` remain the supported entrypoints.
- `cli/main.py` remains a compatibility delegate only.
- Use `cli/launcher.py`, `cli/services/`, and `cli/tui/`.
- TUI screens must not contain backend business logic.
- TUI screens must not call LightRAG directly.
- TUI screens must not call Docker directly.
- Backend authorization remains the source of truth.
- Planned backend gaps must render as gaps, not fake success.

## Tests First

Update or add tests before implementation:

1. Root menu contains `Graphs`, not `LightRAG Graphs`.
2. Root menu contains one `LightRAG Domains` item.
3. Root menu does not contain LightRAG domain CRUD actions.
4. LightRAG Domains screen contains domain CRUD actions.
5. Root menu contains `Documents`, not `Admin Documents`.
6. Documents screen contains admin actions for admin users.
7. Documents screen hides or disables admin actions for normal users.
8. Graph screen still calls existing graph routes.
9. LightRAG domain actions still call existing admin domain routes through `cli/services`.

Run:

```bash
pytest tests/test_cli_tui.py tests/test_cli_screen_renderers.py tests/test_cli_services.py -q
```

If available:

```bash
pytest tests/test_cli_ascii_samples.py -q
```

## Documentation Updates

Update:

```text
docs/cli_docs/tui_ux.md
docs/cli_docs/frontend_traceability.md
docs/cli_docs/commands.md
docs/cli_docs/api-contract.md
```

Make the docs match the new screen hierarchy.

## Acceptance Criteria

The task is complete when:

1. Root menu is shorter and capability-based.
2. LightRAG CRUD is nested under `LightRAG Domains`.
3. `LightRAG Graphs` is renamed to `Graphs`.
4. `Admin Documents` is no longer a top-level duplicate.
5. Admin document actions remain available under `Documents`.
6. Backend routes are not broken or unnecessarily renamed.
7. TUI services still call backend APIs through `ApiClient`.
8. Tests prove the new menu structure.
```
