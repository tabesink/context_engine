# 1. UX Diagnosis

## 1.1 What Is Already Good

The existing ASCII screen plan has the right underlying goal: the terminal UI mirrors backend API surfaces and lets developers/operators see what routes are called, which capabilities are admin-only, and which features are backend gaps.

Strong points:

- Each screen maps to a backend capability.
- Screens show the backend route being called.
- Admin-only surfaces are identified.
- Planned backend gaps are documented instead of pretending they work.
- Retrieval, document, job, graph, and observability surfaces are represented.
- ASCII-style layouts are portable across terminals and good for junior developers.
- The TUI can act as a future browser-frontend traceability prototype.

## 1.2 What Feels Too Cluttered

Some screens show too much route/request/response detail in the main body.

Examples of clutter risks:

- Showing route, request payload, response fields, related commands, and controls all on every default screen.
- Showing long document IDs in default tables.
- Having both `Documents` and `Admin Documents` as root items.
- Having both `LightRAG Domains` and separate root-level LightRAG CRUD actions.
- Showing implementation labels such as `LightRAG Graphs` at the root.
- Putting every possible action directly in a root menu instead of nesting actions inside capability areas.

## 1.3 What Is Missing for API Debugging

The TUI should expose more backend/API detail, but not by default.

Missing or underdeveloped debug affordances:

- A reusable API inspect drawer.
- Raw JSON view for actual backend response.
- Full ID toggle.
- Request payload preview before submit.
- HTTP status and latency in a consistent footer.
- Admin-only debug payload visibility.
- Clear route mapping for multipart upload and DELETE operations.
- A consistent error detail panel with backend route, status code, message, and next action.
- A consistent backend gap panel that states missing route and suggested next implementation step.

## 1.4 Main UX Recommendation

Use progressive disclosure.

```text
Default screen:
  - clean title
  - route/status hint in footer
  - compact table or summary
  - primary actions only

Inspect screen:
  - method and route
  - query params or request payload
  - status code and latency
  - response summary
  - selected IDs
  - raw JSON option
```

This preserves the TUI as a backend/API testing tool without turning every screen into a wall of text.

## 1.5 Label Improvements

| Current Label | Recommended Label | Reason |
|---|---|---|
| `LightRAG Graphs` | `Graphs` | User-facing capability, not implementation detail. |
| `Admin Documents` | `Documents > Admin Actions` | Avoid duplicate top-level document concept. |
| `Create LightRAG Domain` at root | `LightRAG Domains > Create Domain` | CRUD belongs inside the domain screen. |
| `Start LightRAG Domain` at root | `LightRAG Domains > Start Domain` | Same. |
| `Stop LightRAG Domain` at root | `LightRAG Domains > Stop Domain` | Same. |
| `Recreate LightRAG Domain` at root | `LightRAG Domains > Recreate Domain` | Same. |
| `Remove LightRAG Domain` at root | `LightRAG Domains > Archive Remove Domain` | More explicit and safer. |

## 1.6 Final Design Principle

```text
Do not remove information.
Move information to the correct layer.
```

That means:

- root menu = capability areas
- default screen = useful summary
- inspect drawer = route/payload/response details
- raw JSON = full backend shape
- backend gap screen = honest unsupported features
