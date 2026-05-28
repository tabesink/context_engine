# context-engine TUI UX

Launch **`context-engine`** for the interactive Rich terminal layer that rehearses future browser screens. It stays intentionally simple: Rich-only, mostly monochrome, ASCII tables, and shared screen builders under `cli/tui/`.

## Main Menu

```text
CONTEXT ENGINE

Backend: http://127.0.0.1:8000
Session: saved

> Documents
  Retrieval
  Graphs
  LightRAG Domains
  Jobs
  Observability
  Health / Readiness
  Logout
  Quit
```

## Interaction Model

- Clean exit with **`q`** (and standard interrupt handling outside raw modes).
- Screens are reachable via simple keystrokes/menu entries.
- Retrieval accepts a prompt and renders evidence from **`POST /retrieve`**.
- LightRAG domain forms collect only inputs needed by the backend and show API success/errors directly.
- API-backed screens expose progressive disclosure keys: **`I`** Inspect API, **`J`** Raw JSON, **`F`** toggle full IDs, **`R`** refresh, **`B`** back, and **`Q`** quit.
- Inspect views show method, route, status, latency, request payload, response summary, and selected IDs when available.
- Raw JSON is always on demand and redacts tokens/passwords/API keys, truncates long text, and never displays multipart bytes.
- ASCII-friendly tables maximize portability across terminals.
- Color accents live in **`cli/tui/styles.py`** for future refinement.

## Screen Behavior

- Session shows backend/session summaries without leaking tokens.
- Documents mirrors the **`GET /documents`** document library payload, and shows nested **Admin Actions** only for admin users.
- Retrieval mirrors **`POST /retrieve`** only.
- Graphs screens consume backend proxy JSON only—no direct LightRAG SDK.
- LightRAG Domains lists configured domains and exposes nested admin lifecycle actions (create/show/start/stop/recreate/regenerate/archive/permanent delete).
- Recreate and remove flows require typed confirmations; permanent delete is explicit and depends on backend configuration.
- Documents admin actions (upload/list/reingest/refresh-status/delete) call existing `/admin/documents` routes from inside the Documents area.
- Observability stays read-through of backend payloads.
- Backend gaps are documented in `docs/cli_docs/backend_gaps.md`; they are not exposed as a root TUI screen.

## Non-goals

- Widget-heavy TUIs/frameworks unrelated to shipping needs.
- Local business logic skipping FastAPI validations.
- Fake chat/users/runs approvals/corpus lifecycle behavior.
- Local graph visualization beyond summaries + JSON cues.
