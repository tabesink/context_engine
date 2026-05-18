# context-engine TDD Implementation Status

Status for the historical work bundles under **`docs/cli_docs/02_ragcli_tdd_plans/`** (folder name kept).

| Phase | Status | Notes |
|---|---|---|
| Phase 1: Human screen renderers | Partially superseded | Rich TUI + screen builders supersede Typer `human \| json` output paths. Legacy renderer tests may still guard shared tables. |
| Phase 2: Screen models and API boundaries | Implemented | Shared screen builders/actions under **`cli/screens/`** where still referenced. |
| Phase 3: Lightweight TUI | Implemented | Launcher **`context-engine`** / **`context-tui`** (`cli.launcher:main`) + **`cli/tui/`** menus and flows. See **`tests/test_cli_tui.py`**. |
| Phase 4: Guided flows | Partially superseded | Operator flows live inside TUI screens; discrete Typer-guided commands were removed with the TUI-only direction. Traceability matrices remain in **`frontend_traceability.md`**. |
| Phase 5: Frontend traceability docs | Implemented | **`frontend_traceability.md`**, **`tui_ux.md`**, and this status file. |

## Tests Added (current naming)

- **`tests/test_cli_launcher.py`** — parses launcher settings into `CredentialStore` + `run_tui` delegation.
- **`tests/test_cli_tui.py`** — keyboard navigation, authentication, retrieval, uploads, graphs, LightRAG domain lifecycle forms, observability previews.
- **`tests/test_cli_services.py`** — typed HTTP helpers layered on **`ApiClient`**, including LightRAG domain admin route wrappers.
- **`tests/test_cli_screen_renderers.py`** / **`tests/test_cli_query_payload.py`** — ancillary rendering + payload regressions while those modules survive.

```bash
python -m pytest tests/test_cli_launcher.py tests/test_cli_services.py tests/test_cli_tui.py tests/test_cli_screen_renderers.py tests/test_cli_query_payload.py
python -m pytest
```

## Remaining constraints

- Backend gaps must stay explicit (**`not_supported_by_backend`** or equivalent UX)—never fabricated success locally.
- The shipping binary is deliberately lightweight (**Rich + keystrokes**) versus a heavyweight widget framework.
- LightRAG domain deployment needs backend configuration (`LIGHTRAG_DEPLOY_ENABLED`, Docker/image/storage settings); TUI tests assert client behavior and backend tests assert deploy behavior.
