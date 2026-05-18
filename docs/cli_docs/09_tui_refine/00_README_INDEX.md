# Context Engine CLI/TUI UX Refinement Package

## Purpose

This package refines the Context Engine terminal UI so it works as both:

1. a clean human operator interface, and
2. a backend/API testing console for inspecting request inputs, response shapes, IDs, statuses, route mappings, backend gaps, and errors.

The key UX rule is:

```text
Default view = clean operator summary.
Inspect/debug view = backend/API visibility.
```

The CLI should not become cluttered by showing every payload and response field by default. Instead, each screen should expose enough information to operate normally, while deeper backend/API detail is available through explicit inspect modes.

## Current Direction Assumptions

- Supported launcher commands are `context-engine` and `context-tui`.
- Do not design around legacy `ragcli` as the main UX.
- `cli/main.py` remains a compatibility delegate only.
- TUI screens live under `cli/tui/`.
- API call helpers live under `cli/services/`.
- `cli/services/*` calls backend routes through `cli/api_client.py`.
- TUI screens must not call backend business logic directly.
- TUI screens must not call LightRAG directly.
- TUI screens must not call Docker directly.
- The backend remains the source of truth for auth, permissions, route behavior, and errors.

## Final UX Intent

Root menu:

```text
CONTEXT ENGINE

Backend: http://127.0.0.1:8010
Session: admin@example.com
Role:    admin

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

Core interaction keys:

```text
↑/↓  Move
Enter Select
R    Refresh
I    Inspect API
J    Raw JSON
F    Toggle full IDs
D    Debug details, admin only
B    Back
Q    Quit
```

## Files in This Package

| File | Purpose |
|---|---|
| `01_ux_diagnosis.md` | What is good, what is cluttered, and what needs refinement. |
| `02_root_menu_and_navigation.md` | Final root menu, role-aware visibility, nested navigation model. |
| `03_global_screen_template.md` | Reusable screen chrome, footer, route/status hints, keyboard model. |
| `04_progressive_disclosure.md` | Inspect API drawer, raw JSON view, full ID toggle, debug mode. |
| `05_screen_specific_refinements.md` | Documents, Retrieval, Graphs, LightRAG Domains, Jobs, Observability, Health, Backend Gaps. |
| `06_error_gap_security_ux.md` | Error panels, backend gap UX, sensitive output rules. |
| `07_traceability_matrix.md` | Screen-to-route matrix with default view and inspect view guidance. |
| `08_tdd_implementation_plan.md` | TDD slices, files to modify, tests, acceptance criteria. |
| `09_coding_agent_prompt.md` | Ready-to-use implementation prompt for a coding agent. |
| `context_engine_cli_tui_ux_refinement_combined.md` | Combined report. |
