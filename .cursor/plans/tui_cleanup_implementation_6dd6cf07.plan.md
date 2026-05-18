---
name: tui cleanup implementation
overview: Implement the `08_tui_cleanup` target UX using strict test-first vertical slices, then align CLI docs with the final shipped TUI structure and API mappings.
todos:
  - id: tdd-root-menu
    content: Write/adjust root-menu tests first, then implement capability-only root menu and Graphs rename.
    status: completed
  - id: tdd-domains-nesting
    content: Write/adjust domain nesting tests first, then move domain lifecycle actions under LightRAG Domains screen.
    status: completed
  - id: tdd-documents-consolidation
    content: Write/adjust documents/admin tests first, then fold admin actions under Documents with role-aware visibility.
    status: completed
  - id: regression-tests
    content: Run targeted CLI/TUI/service test suites and resolve regressions introduced by menu/screen rewiring.
    status: completed
  - id: docs-sync
    content: Update CLI docs set (tui_ux, traceability, commands, api-contract, README) to reflect final shipped TUI state.
    status: completed
isProject: false
---

# Implement TUI Cleanup + CLI Docs Sync

## Scope and outcome
- Apply the `docs/cli_docs/08_tui_cleanup` decisions to the active TUI runtime so root navigation is capability-based, LightRAG domain CRUD is nested, and document admin actions are folded under Documents.
- Keep backend API contracts unchanged; only TUI structure/labels/flow wiring and docs are updated.
- Execute via TDD tracer bullets (one behavior per RED→GREEN cycle), then refactor lightly.

## Code areas to change
- Root menu + routing: [`cli/tui/screens/main_menu.py`](cli/tui/screens/main_menu.py), [`cli/tui/menu.py`](cli/tui/menu.py)
- Screen composition and labels: [`cli/tui/screens/content.py`](cli/tui/screens/content.py)
- Domain screen action set/table semantics if needed: [`cli/screens/lightrag_domains.py`](cli/screens/lightrag_domains.py)
- Existing service wrappers (verify unchanged route mapping): [`cli/services/lightrag_domains.py`](cli/services/lightrag_domains.py)

## TDD implementation slices
1. **Root menu cleanup**
   - RED: update/add tests asserting root menu contains `Documents`, `Retrieval`, `Graphs`, `LightRAG Domains`, and excludes `LightRAG Graphs`, `Admin Documents`, and root-level domain CRUD actions.
   - GREEN: adjust menu item definitions and ordering to match target capability-only root menu.

2. **Graphs rename (UI-only)**
   - RED: assert rendered menu/screen titles use `Graphs` / `GRAPHS` and no longer show `LightRAG Graphs`.
   - GREEN: rename labels/breadcrumb/title text only; preserve existing graph service route calls (`/graphs`, `/graph/label/*`).

3. **LightRAG domain action nesting**
   - RED: assert `LightRAG Domains` screen shows lifecycle actions (`Create`, `Show detail`, `Start`, `Stop`, `Recreate`, `Regenerate`, `Archive remove`, `Permanent delete`) and root no longer exposes those as top-level items.
   - GREEN: move/compose current domain operation screens behind the domain area and keep `LightRAGDomainService` route usage unchanged.

4. **Documents consolidation**
   - RED: assert `Admin Documents` is removed from root, and Documents area exposes admin actions for admin users while non-admin users see hidden/disabled admin actions per current role model.
   - GREEN: nest upload/list/index/reindex/delete flows under Documents and update breadcrumbs to reflect `Documents > Admin Actions` instead of top-level Admin Documents.

5. **Regression pass**
   - Run focused suites and fix drift:
     - `tests/test_cli_tui.py`
     - `tests/test_cli_screen_renderers.py`
     - `tests/test_cli_services.py`
     - optional ASCII/conformance tests if present.

## Documentation sync (reflect shipped behavior)
- Update menu/flow and naming in:
  - [`docs/cli_docs/tui_ux.md`](docs/cli_docs/tui_ux.md)
  - [`docs/cli_docs/frontend_traceability.md`](docs/cli_docs/frontend_traceability.md)
  - [`docs/cli_docs/commands.md`](docs/cli_docs/commands.md)
  - [`docs/cli_docs/api-contract.md`](docs/cli_docs/api-contract.md)
  - [`docs/cli_docs/README.md`](docs/cli_docs/README.md)
- Ensure docs consistently state:
  - Supported entrypoints are `context-engine` / `context-tui`
  - Root menu is capability-based
  - `Graphs` (not `LightRAG Graphs`) in operator UX
  - LightRAG domain CRUD is under `LightRAG Domains`
  - Document admin routes remain distinct backend endpoints, surfaced under Documents UI

## Acceptance criteria
- Root menu exactly matches capability-area structure from `08_tui_cleanup`.
- Graph label rename is complete in UX text, with backend graph routes unchanged.
- No top-level `Admin Documents`; equivalent admin capabilities are reachable under Documents.
- No root-level LightRAG domain CRUD actions; lifecycle actions are inside `LightRAG Domains`.
- Tests pass for updated menu/navigation and service-route expectations.
- CLI docs match actual runtime labels/flows and API mappings.
