# ragcli TDD Implementation Status

Status for the work described in `docs/cli_docs/02_ragcli_tdd_plans`.

| Phase | Status | Notes |
|---|---|---|
| Phase 1: Human screen renderers | Implemented | Supported human commands now render through ASCII tables/screen-like layouts where useful. Existing JSON branches remain explicit and stable. |
| Phase 2: Screen models and API boundaries | Implemented | Added `ScreenAction`, `ScreenSection`, `ScreenResult`, and side-effect-free screen builders under `cli/screens`. |
| Phase 3: Lightweight TUI | Implemented | Added Rich-only `ragcli ui` with menu, document/retrieval/admin/jobs/observability/gap screens, and smoke tests. |
| Phase 4: Guided flows | Implemented | Added retrieval compare, admin upload-flow, admin dashboard, and screen aliases. |
| Phase 5: Frontend traceability docs | Implemented | Added this status file, `frontend_traceability.md`, and `tui_ux.md`. |

## Tests Added

- Renderer tests for ASCII tables, screen rendering, secret redaction, backend gap screens, retrieval builders, and job retry actions.
- CLI behavior tests for human document/retrieval/query/graph output, retrieval compare, upload-flow, dashboard, and screen aliases.
- TUI smoke tests for startup/exit, documents, retrieval, and backend gaps.

## Verification Commands

```bash
python -m pytest tests/test_cli_screen_renderers.py tests/test_cli_tui.py tests/test_cli.py tests/test_cli_query_payload.py
python -m pytest
```

## Remaining Constraints

- Planned commands still return `not_supported_by_backend` until backend routes exist.
- `ragcli ui` is intentionally lightweight and input-driven rather than a full Textual application.
- Screen aliases are human-screen helpers; JSON output is only retained for existing stable command contracts and selected guided flows.
