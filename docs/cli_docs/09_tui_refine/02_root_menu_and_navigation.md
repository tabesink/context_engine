# 2. Root Menu and Navigation

## 2.1 Admin Root Menu

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

## 2.2 Normal User Root Menu

```text
CONTEXT ENGINE

Backend: http://127.0.0.1:8010
Session: user@example.com
Role:    user

> Documents
  Retrieval
  Graphs
  Health / Readiness
  Logout
  Quit
```

## 2.3 Role Visibility

| Item | Normal User | Admin | Notes |
|---|---:|---:|---|
| Documents | Yes | Yes | Admin sees nested admin actions. |
| Retrieval | Yes | Yes | Domain selection available if backend supports it. |
| Graphs | Yes | Yes | Backend controls LightRAG availability. |
| LightRAG Domains | No | Yes | Admin deployment/control surface. |
| Jobs | No | Yes | Admin-only indexing job monitor. |
| Observability | No | Yes | Audit/query logs are admin-only. |
| Health / Readiness | Yes | Yes | User-safe subset can be shown to normal users. |
| Backend Gaps | Dev only | Dev only | Hide in production unless useful for debugging. |
| Logout | Yes | Yes | Local session clear. |
| Quit | Yes | Yes | Exit TUI. |

## 2.4 Navigation Hierarchy

```text
Root
  ├── Documents
  │     ├── Browse Ready Documents
  │     ├── Document Detail
  │     ├── Structure / Outline
  │     ├── Page Preview
  │     └── Admin Actions
  │           ├── Upload Document
  │           ├── List All Documents
  │           ├── Index / Reindex
  │           └── Delete Document
  │
  ├── Retrieval
  │     ├── Retrieval Preview
  │     ├── Citation Answer
  │     ├── Compare Modes
  │     └── Domain Selector
  │
  ├── Graphs
  │     ├── Popular Labels
  │     ├── Search Labels
  │     ├── Label Catalog
  │     └── Graph Summary
  │
  ├── LightRAG Domains
  │     ├── List Domains
  │     ├── Create Domain
  │     ├── Show Domain Detail
  │     ├── Start Domain
  │     ├── Stop Domain
  │     ├── Recreate Domain
  │     ├── Regenerate Domain Files
  │     ├── Archive Remove Domain
  │     └── Permanent Delete Domain
  │
  ├── Jobs
  │     ├── List Jobs
  │     ├── Job Detail
  │     └── Retry Failed Job
  │
  ├── Observability
  │     ├── Query Logs
  │     └── Audit Logs
  │
  ├── Health / Readiness
  │     ├── API Health
  │     ├── Readiness
  │     ├── Storage Status
  │     ├── Worker / Redis Status
  │     ├── LightRAG Runtime Status
  │     └── LightRAG Deploy Status
  │
  └── Backend Gaps
```

## 2.5 Root Menu Rules

- Root menu should contain no direct CRUD actions.
- Root menu should contain no duplicate domain concepts.
- Root menu should use user-facing labels, not implementation labels.
- Root menu should hide admin-only areas when user role is known.
- Backend still enforces authorization. UI hiding is convenience only.
- Development-only screens should be clearly labeled and optionally hidden outside local/dev mode.
