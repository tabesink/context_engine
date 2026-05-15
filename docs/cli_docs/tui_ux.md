# ragcli TUI UX

`ragcli ui` is a lightweight terminal rehearsal layer for future frontend screens. It is intentionally simple: Rich-only, mostly monochrome, ASCII tables, and shared screen builders.

## Main Menu

```text
CONTEXT ENGINE

Backend: http://127.0.0.1:8000
Session: saved

[1] Session
[2] Documents
[3] Retrieval
[4] LightRAG Graphs
[5] Admin Documents
[6] Jobs
[7] Observability
[8] Backend Gaps
[Q] Quit
```

## Interaction Model

- The TUI starts and exits cleanly with `q`.
- Screens are selected by simple key input.
- Retrieval accepts one query and renders evidence from `POST /query/retrieve`.
- Tables use ASCII borders so output is portable across terminals.
- Color is reserved for future semantic accents and is centralized in `cli/tui/styles.py`.

## Screen Behavior

- Session shows backend/session summary without exposing tokens.
- Documents renders the same document library model used by `ragcli documents list`.
- Retrieval renders the same retrieval model used by `ragcli documents retrieve`.
- LightRAG renders backend label/graph API data only; it never uses a direct LightRAG client.
- Admin Documents and Observability render backend responses without local authorization decisions.
- Backend Gaps lists planned unsupported surfaces as `not_supported_by_backend`.

## Non-goals

- No widget-heavy framework.
- No local business logic that bypasses backend APIs.
- No fake chat, users, runs, approvals, or corpus lifecycle behavior.
- No terminal graph visualization beyond summaries and JSON export hints.
