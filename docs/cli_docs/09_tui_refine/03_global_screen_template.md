# 3. Global Screen Template

## 3.1 Standard Screen Layout

```text
┌──────────────────────────────────────────────────────────────┐
│ CONTEXT ENGINE / Documents                                   │
│ Backend: http://127.0.0.1:8010   User: admin@example.com      │
├──────────────────────────────────────────────────────────────┤
│ Summary / Data                                               │
│                                                              │
│ +------------+-------------+---------+---------+-------------+
│ | id         | filename    | status  | pages   | updated     |
│ +------------+-------------+---------+---------+-------------+
│ | doc_01f... | manual.pdf  | ready   | 124     | 2026-05-18  |
│ +------------+-------------+---------+---------+-------------+
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ Actions                                                      │
│ > Open selected                                              │
│   Refresh                                                    │
│   Inspect API                                                │
│   Back                                                       │
├──────────────────────────────────────────────────────────────┤
│ Route: GET /documents        Status: 200       Time: 42 ms   │
│ Keys: ↑/↓ Move  Enter Select  I Inspect  R Refresh  B Back   │
└──────────────────────────────────────────────────────────────┘
```

## 3.2 Screen Regions

| Region | Purpose | Rule |
|---|---|---|
| Header | Screen title and breadcrumb. | Keep one or two lines. |
| Session strip | Backend URL and user/session. | Do not show token. |
| Main body | Table, result, form, or message. | Maximize signal, reduce boilerplate. |
| Actions | Available next actions. | 3–8 actions max. |
| Route footer | Method/path/status/latency. | Compact one-line hint. |
| Key footer | Common controls. | Consistent across screens. |

## 3.3 Route Footer

Every API-backed screen should show a compact route footer:

```text
Route: POST /query/retrieve    Status: 200    Time: 63 ms
```

For local-only screens:

```text
Local: credential store clear    Status: done
```

For backend gaps:

```text
Route: none    Status: backend gap
```

## 3.4 Keyboard Model

| Key | Meaning |
|---|---|
| `↑/↓` | Move selection. |
| `Enter` | Select / submit. |
| `R` | Refresh current API-backed screen. |
| `I` | Inspect API request/response. |
| `J` | Raw JSON response. |
| `F` | Toggle full IDs. |
| `D` | Debug details, admin-only. |
| `B` | Back. |
| `Q` | Quit. |

## 3.5 Table Rules

Default tables should show only useful columns.

Rules:

- 5–7 columns max.
- ID columns truncated by default.
- Dates shortened by default.
- Avoid wide JSON blobs in tables.
- Avoid showing metadata dicts in tables.
- Use `F` to reveal full IDs.
- Use `I` or `J` for full payloads.

## 3.6 Empty State Template

```text
┌──────────────────────────────────────────────────────────────┐
│ CONTEXT ENGINE / Documents                                   │
├──────────────────────────────────────────────────────────────┤
│ No documents found.                                          │
│                                                              │
│ Next:                                                        │
│ > Refresh                                                    │
│   Upload Document       admin only                           │
│   Back                                                       │
├──────────────────────────────────────────────────────────────┤
│ Route: GET /documents        Status: 200       Time: 28 ms   │
│ Keys: Enter Select  R Refresh  I Inspect  B Back             │
└──────────────────────────────────────────────────────────────┘
```

## 3.7 Loading State Template

```text
CONTEXT ENGINE / Retrieval

Loading...
Route: POST /query/retrieve
```

Keep loading states simple.

## 3.8 Error State Template

```text
ERROR

code:    forbidden
message: Admin access required
route:   POST /admin/documents/upload
status:  403

Next:
> Back
  Check current session
```

No stack traces by default.
