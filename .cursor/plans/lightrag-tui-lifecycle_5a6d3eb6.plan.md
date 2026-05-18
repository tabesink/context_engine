---
name: lightrag-tui-lifecycle
overview: Add full interactive LightRAG domain lifecycle management to the TUI CLI using vertical TDD slices, then update the CLI documentation to match the new TUI-first surface and LightRAG deploy environment requirements.
todos:
  - id: create-flow
    content: Add TDD slice for Create LightRAG Domain TUI flow and implement the screen.
    status: completed
  - id: operation-flows
    content: Add TDD slices and implementation for start, stop, and recreate domain screens.
    status: completed
  - id: remove-flow
    content: Add archive and permanent delete TDD slices with explicit confirmation handling.
    status: completed
  - id: menu-navigation
    content: Wire separate LightRAG domain lifecycle entries into the TUI menu/navigation.
    status: completed
  - id: docs-update
    content: Update CLI docs to match the implemented TUI lifecycle and LightRAG env prerequisites.
    status: completed
  - id: verification
    content: Run focused tests and lints for edited files.
    status: completed
isProject: false
---

# LightRAG TUI Domain Lifecycle Plan

## Current State
- Backend admin routes already exist in [app/api/routes/lightrag_admin.py](app/api/routes/lightrag_admin.py): list, create, detail, up, down, recreate, regenerate, and delete with optional `permanent=true`.
- CLI service wrappers already exist in [cli/services/lightrag_domains.py](cli/services/lightrag_domains.py).
- The TUI currently has a LightRAG Domains read/list screen through [cli/tui/screens/content.py](cli/tui/screens/content.py), but no interactive lifecycle flows.
- [`.env.example`](.env.example) already includes `LIGHTRAG_API_KEY` and most deploy settings; docs should clarify runtime vs deploy variables and the `LIGHTRAG_DOMAIN_MANIFEST` vs `LIGHTRAG_DOMAINS_MANIFEST` distinction.

## Target UX
Use separate TUI menu entries/screens for each lifecycle action:
- `LightRAG Domains`: list/read screen remains the overview.
- `Create LightRAG Domain`: prompt for `domain_id`, optional `display_name`, optional `host_port`, and `make_default`.
- `Start LightRAG Domain`: choose/enter domain id, call `/up`, show operation result.
- `Stop LightRAG Domain`: choose/enter domain id, call `/down`, show operation result.
- `Recreate LightRAG Domain`: choose/enter domain id, require confirmation, call `/recreate`.
- `Remove LightRAG Domain`: choose/enter domain id, support archive by default and permanent delete behind explicit confirmation; surface backend errors when permanent deletion is disabled.

## Implementation Approach
- Reuse `TuiState.lightrag_domain_service()` and the existing `LightRAGDomainService` methods instead of adding new HTTP plumbing.
- Add small form/action screens under [cli/tui/screens/content.py](cli/tui/screens/content.py), following existing `ApiResultScreen` and prompt screen conventions.
- Add menu entries in [cli/tui/screens/main_menu.py](cli/tui/screens/main_menu.py) and route them from [cli/tui/app.py](cli/tui/app.py) if needed by the current stack/navigation pattern.
- Keep validation close to user input: require non-empty domain ids, parse optional ports as integers, parse yes/no confirmations before destructive actions, and let backend validation messages pass through clearly.
- Preserve admin auth behavior: failed `401/403/400/404` responses should render as TUI errors through existing `ApiClientError`/screen error handling.

## TDD Slices
1. Add a failing TUI test for the `Create LightRAG Domain` menu flow in [tests/test_cli_tui.py](tests/test_cli_tui.py), then implement the minimal screen that posts the expected payload.
2. Add one lifecycle operation test for `Start LightRAG Domain`, then generalize only enough to support shared domain-id operation screens.
3. Add `Stop LightRAG Domain` and `Recreate LightRAG Domain` tests one at a time; add confirmation behavior for recreate before the call is made.
4. Add archive remove test, then permanent remove test with explicit confirmation and `?permanent=true` path assertion.
5. Add service-level route coverage in [tests/test_cli_services.py](tests/test_cli_services.py) only if current assertions do not already cover the needed methods and query strings.
6. Run focused tests after each green slice, then run the broader CLI/TUI test set before docs updates.

## Documentation Updates
After implementation, update CLI docs to describe the actual TUI-first lifecycle:
- [docs/cli_docs/README.md](docs/cli_docs/README.md): add LightRAG domain lifecycle capability and env prerequisite pointers.
- [docs/cli_docs/commands.md](docs/cli_docs/commands.md): map each TUI action to backend method/path.
- [docs/cli_docs/api-contract.md](docs/cli_docs/api-contract.md): document `/lightrag/domains` and `/admin/lightrag/domains*` request/response shapes.
- [docs/cli_docs/tui_ux.md](docs/cli_docs/tui_ux.md): update menu and screen behavior.
- [docs/cli_docs/frontend_traceability.md](docs/cli_docs/frontend_traceability.md): trace domain lifecycle and retrieval domain selection to API paths.
- [docs/cli_docs/tdd_implementation_status.md](docs/cli_docs/tdd_implementation_status.md): record the TDD slices and current coverage.
- [docs/cli_docs/07_tui_only/tui_only.md](docs/cli_docs/07_tui_only/tui_only.md): refresh TUI-only plan references and include `cli/services/lightrag_domains.py`.

## Verification
- Run focused tests while implementing: `pytest tests/test_cli_tui.py tests/test_cli_services.py`.
- Run API/domain tests if docs or behavior touch backend assumptions: `pytest tests/test_api.py tests/test_lightrag_deploy_service.py tests/test_lightrag_deploy_manifest_compose.py`.
- Use `ReadLints` on edited Python files after substantive edits.
- Verify CLI docs no longer describe LightRAG domain admin as future-only or subcommand-first.