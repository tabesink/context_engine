# 8. TDD Implementation Plan

## Slice 1: Root Menu Cleanup

### Tests

- root menu includes `Documents`
- root menu includes `Retrieval`
- root menu includes `Graphs`
- root menu includes `LightRAG Domains` for admin
- root menu does not include `LightRAG Graphs`
- root menu does not include `Admin Documents`
- root menu does not include LightRAG domain CRUD actions

### Files

```text
cli/tui/screens/main_menu.py
cli/tui/state.py
tests/test_cli_tui.py
tests/test_cli_screen_renderers.py
```

## Slice 2: Shared Screen Chrome

### Tests

- screen footer shows route/status/latency
- local-only screen says local only
- backend gap screen says backend gap
- key hints include `I`, `J`, `F`, `R`, `B`, `Q`

### Files

```text
cli/tui/renderers/
cli/tui/styles.py
tests/test_cli_screen_renderers.py
```

## Slice 3: API Inspect Drawer

### Tests

- GET inspect drawer renders method/route/status/latency
- POST inspect drawer renders request JSON
- multipart inspect drawer hides bytes
- DELETE inspect drawer shows confirmation/payload
- secrets are redacted

### Files

```text
cli/tui/renderers/inspect.py
cli/tui/screens/*
tests/test_cli_screen_renderers.py
```

## Slice 4: Raw JSON Viewer

### Tests

- raw JSON pretty-prints response
- token/password/api_key fields are redacted
- long content fields are truncated
- full IDs can be toggled

### Files

```text
cli/tui/renderers/json_view.py
tests/test_cli_screen_renderers.py
```

## Slice 5: Documents/Admin Consolidation

### Tests

- root does not show `Admin Documents`
- Documents screen shows admin actions for admin
- Documents screen hides admin actions for normal user
- admin actions call `/admin/documents...`
- browse actions call `/documents...`

### Files

```text
cli/tui/screens/documents.py
cli/services/documents.py
cli/services/admin_documents.py
tests/test_cli_tui.py
tests/test_cli_services.py
```

## Slice 6: Retrieval Debug Visibility

### Tests

- retrieval screen includes query/mode/top_k/domain/document filters
- inspect mode shows exact request payload
- result table shows engine/score/pages/section/document
- raw JSON available

### Files

```text
cli/tui/screens/retrieval.py
cli/services/query.py
cli/query_payload.py
tests/test_cli_query_payload.py
tests/test_cli_tui.py
```

## Slice 7: Graphs Rename

### Tests

- root menu shows `Graphs`
- graph screen title is `GRAPHS`
- graph service still calls `/graphs` and `/graph/label/...`

### Files

```text
cli/tui/screens/graphs.py
cli/services/lightrag.py
tests/test_cli_tui.py
tests/test_cli_services.py
```

## Slice 8: LightRAG Domains Nested CRUD

### Tests

- root has only `LightRAG Domains`
- LightRAG Domains screen includes create/start/stop/recreate/remove
- TUI service calls `/admin/lightrag/domains...`
- permanent delete requires typed confirmation

### Files

```text
cli/tui/screens/lightrag_domains.py
cli/services/lightrag_domains.py
tests/test_cli_tui.py
tests/test_cli_services.py
```

## Slice 9: Health / Readiness

### Tests

- health screen calls `/health`
- readiness screen calls `/health/readiness`
- status rows show check/status/detail
- unavailable checks render warning, not fake OK

### Files

```text
cli/tui/screens/health.py
cli/services/health.py
tests/test_cli_tui.py
tests/test_cli_services.py
```

## Slice 10: Backend Gaps Cleanup

### Tests

- backend gaps show capability/missing route/priority/note
- unsupported capabilities do not call fake backend success routes
- gap screen recommends backend-first implementation path

### Files

```text
cli/tui/screens/backend_gaps.py
cli/screens/planned.py
tests/test_cli_tui.py
```

## Slice 11: Documentation Update

Update:

```text
docs/cli_docs/tui_ux.md
docs/cli_docs/frontend_traceability.md
docs/cli_docs/api-contract.md
docs/cli_docs/ascii_render_conformance.md
```

## Slice 12: Test Commands

Run:

```bash
pytest tests/test_cli_tui.py tests/test_cli_services.py tests/test_cli_screen_renderers.py -q
```

If ASCII conformance tests exist:

```bash
pytest tests/test_cli_ascii_samples.py -q
```

## Acceptance Criteria

- Default screens are clean and not cluttered.
- Every API-backed screen has inspect mode.
- Raw JSON is available but hidden by default.
- Root menu is capability-based.
- Admin actions are nested, not duplicated at root.
- Graphs label no longer leaks LightRAG implementation.
- LightRAG domain CRUD is under LightRAG Domains.
- TUI stays a thin client over backend API.
- Tests prove route mapping and render behavior.
