---
name: tui-refine-tdd
overview: Implement the `docs/cli_docs/09_tui_refine` UX refinement with vertical TDD slices against the existing Rich TUI architecture, keeping screens as thin API clients and moving backend gap visibility out of the CLI into documentation.
todos:
  - id: root-menu-gap-doc
    content: "Red-green Slice 1: remove Backend Gaps from TUI root and create/update backend gaps documentation."
    status: completed
  - id: keys-chrome
    content: "Red-green Slice 2: add global key normalization and shared route/status/latency footer chrome."
    status: completed
  - id: api-metadata
    content: "Red-green Slice 3: add non-breaking API request metadata for inspect/raw views."
    status: completed
  - id: inspect-json
    content: "Red-green Slice 4: add inspect drawer, raw JSON view, redaction, truncation, and full-ID toggle."
    status: completed
  - id: documents-retrieval
    content: "Red-green Slices 5-6: refine Documents/Admin consolidation and retrieval inspect/debug visibility."
    status: completed
  - id: graphs-domains-health
    content: "Red-green Slices 7-9: refine Graphs, LightRAG Domains, Health/Readiness, Jobs, and Observability states."
    status: completed
  - id: docs-verify
    content: Update CLI docs and run focused plus full CLI/TUI verification commands.
    status: completed
isProject: false
---

# TUI Refine TDD Implementation

## Decisions Applied
- Root menu keeps role-allowed items visible with honest disabled/unavailable states when backend features are unavailable.
- `Backend Gaps` is removed from CLI navigation; unsupported backend/API surfaces move to a durable doc such as [docs/cli_docs/backend_gaps.md](docs/cli_docs/backend_gaps.md).
- Keep implementation aligned with the current layout: [cli/tui/screens/main_menu.py](cli/tui/screens/main_menu.py), [cli/tui/screens/content.py](cli/tui/screens/content.py), [cli/tui/styles.py](cli/tui/styles.py), [cli/tui/keys.py](cli/tui/keys.py), [cli/api_client.py](cli/api_client.py), and existing [cli/screens/](cli/screens/) builders. Avoid a broad screen-file split unless a slice forces it.

## TDD Strategy
Use vertical red-green-refactor slices. For each behavior, add one failing public-interface test, implement only enough to pass, then refactor if duplication appears. Primary commands:

```bash
pytest tests/test_cli_tui.py tests/test_cli_services.py tests/test_cli_screen_renderers.py -q
pytest tests/test_cli_query_payload.py -q
```

## Implementation Plan
1. Root menu cleanup and gap removal:
- Update tests in [tests/test_cli_tui.py](tests/test_cli_tui.py) so admin root no longer expects `Backend Gaps`, still expects `Documents`, `Retrieval`, `Graphs`, `LightRAG Domains`, `Jobs`, `Observability`, `Health / Readiness`, `Logout`, and `Quit`.
- Remove `BackendGapsScreen` from [cli/tui/screens/main_menu.py](cli/tui/screens/main_menu.py) root wiring while preserving existing non-admin hiding.
- Add or update a docs file listing backend gaps from [cli/screens/planned.py](cli/screens/planned.py), instead of exposing that list in the TUI.

2. Global keys and shared screen chrome:
- Add tests for normalized `I`, `J`, `F`, `D`, and plain `R` in [tests/test_cli_tui.py](tests/test_cli_tui.py).
- Extend [cli/tui/keys.py](cli/tui/keys.py) and [cli/tui/styles.py](cli/tui/styles.py) with a common footer/chrome helper that can render route, status, latency, and the global key hints.
- Keep existing `Ctrl+R` compatibility while showing `R Refresh` in the UI.

3. API call metadata for inspect mode:
- Add tests against fake client/service behavior before changing implementation.
- Extend [cli/api_client.py](cli/api_client.py) with non-breaking last-request metadata: method, route, status code, elapsed ms, sanitized request summary, sanitized response summary. Existing `get/post/delete/post_file` should still return parsed JSON.
- Ensure multipart uploads record filename/field/fields/content size only, never bytes.

4. Inspect drawer and raw JSON views:
- Add small rendering helpers, likely under [cli/tui/renderers/](cli/tui/renderers/) if the behavior is TUI-specific, while keeping ASCII builder rendering under [cli/renderers/](cli/renderers/).
- Test redaction for `token`, `password`, `api_key`, `Authorization`, local secret-ish fields, and long content truncation in [tests/test_cli_screen_renderers.py](tests/test_cli_screen_renderers.py).
- Wire `I`, `J`, `F`, and admin-only `D` into `ApiResultScreen`, retrieval result screens, upload result screens, LightRAG domain result screens, health, jobs, observability, and graphs where payload/API metadata exists.

5. Documents/Admin consolidation polish:
- Add focused tests that `Admin Documents` is absent at root, `Documents` shows nested admin actions for admins, hides them for users, read browsing calls `/documents`, and admin actions call `/admin/documents...`.
- Update [cli/tui/screens/content.py](cli/tui/screens/content.py), [cli/services/documents.py](cli/services/documents.py), and [cli/services/admin_documents.py](cli/services/admin_documents.py) only where behavior or labels diverge.

6. Retrieval inspect/debug behavior:
- Add one behavior test at a time for retrieval request fields: query, mode, `top_k`, LightRAG domain, document filter, fallback, and debug request.
- Ensure inspect mode shows the exact payload sent through [cli/query_payload.py](cli/query_payload.py) and [cli/services/retrieval.py](cli/services/retrieval.py).
- Result defaults stay clean: engine, score, pages, document, section; evidence IDs move to inspect/raw/full-ID views.

7. Graphs and LightRAG Domains:
- Keep root label `Graphs`; service calls remain `/graphs` and `/graph/label/...` through [cli/services/lightrag.py](cli/services/lightrag.py).
- Keep `LightRAG Domains` admin-only at root, with nested create/start/stop/recreate/regenerate/archive/permanent delete flows through [cli/services/lightrag_domains.py](cli/services/lightrag_domains.py).
- Add disabled/unavailable render tests for backend feature failures without hiding the role-allowed menu item.

8. Health / Readiness and observability:
- Test that health calls `/health` and readiness calls `/health/readiness`, rendering real returned checks and warnings for unavailable checks.
- Do not fake Docker/worker/LightRAG details if the backend does not return them.
- Keep observability default minimal and move metadata into inspect/raw views.

9. Documentation updates:
- Update [docs/cli_docs/tui_ux.md](docs/cli_docs/tui_ux.md), [docs/cli_docs/frontend_traceability.md](docs/cli_docs/frontend_traceability.md), [docs/cli_docs/api-contract.md](docs/cli_docs/api-contract.md), and [docs/cli_docs/ascii_render_conformance.md](docs/cli_docs/ascii_render_conformance.md) to match the implemented labels, key model, inspect/raw behavior, and backend gap doc.

## Verification
- Run focused tests after each slice, then the full CLI/TUI test set.
- Use [ReadLints](ReadLints) on edited Python files after substantive edits.
- Do not commit or push unless explicitly asked.