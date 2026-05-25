# 1. Decisions and Rationale

## 1.1 Problem

The current post-login menu is too flat:

```text
Documents
Retrieval
LightRAG Graphs
Admin Documents
Jobs
Observability
Health / Readiness
Backend Gaps
Logout
Quit
LightRAG Domains
Create LightRAG Domain
Start LightRAG Domain
Stop LightRAG Domain
Recreate LightRAG Domain
Remove LightRAG Domain
```

Problems:

1. `LightRAG Domains` exists as a menu item, but its CRUD actions also appear separately at the root.
2. `LightRAG Graphs` exposes implementation detail in the top-level label.
3. `Documents` and `Admin Documents` look like duplicate concepts even though they call different APIs.
4. Root menu grows as features are added, making the TUI harder for operators and junior developers to reason about.

## 1.2 Decision: Root Menu Should Show Capability Areas, Not Individual Actions

The root menu should show major app areas:

```text
Documents
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

Each area owns its own actions.

## 1.3 Decision: Move LightRAG Domain CRUD Inside LightRAG Domains

LightRAG domain lifecycle actions belong inside one screen:

```text
LightRAG Domains
  ├── List Domains
  ├── Create Domain
  ├── Start Domain
  ├── Stop Domain
  ├── Recreate Domain
  ├── Regenerate Domain Files
  ├── Archive Remove
  └── Permanent Delete
```

This matches the architecture decision that LightRAG domain deployment is a small admin-control feature inside Context Engine, not a separate app or command cluster.

## 1.4 Decision: Rename LightRAG Graphs to Graphs

Use operator-facing language at the root.

Old:

```text
LightRAG Graphs
```

New:

```text
Graphs
```

Reason:

- Operators care that they are exploring graph labels/entities/relations.
- The implementation happens to be LightRAG-backed today.
- Keeping implementation names out of root labels makes future backend swaps easier.

Internally, the screen may still show:

```text
Graphs
Powered by configured LightRAG domain
```

## 1.5 Decision: Fold Admin Documents Into Documents

`Documents` and `Admin Documents` are not identical in the backend, but they should not both be top-level items.

Recommended UI:

```text
Documents
  ├── Browse Documents
  ├── Document Detail
  ├── Structure / Outline
  ├── Page Preview
  └── Admin Actions        # visible only for admins
        ├── Upload Document
        ├── List All Documents
        ├── Reingest / Refresh Status
        └── Delete Document
```

This preserves the backend distinction while reducing UI duplication.

## 1.6 Why Not Merge Backend Routes First?

Do not merge backend routes as part of this TUI cleanup.

Reason:

- `/documents` is a user-safe read surface.
- `/admin/documents` is an admin management surface.
- The TUI can unify them visually without destabilizing backend contracts.
- Backend route simplification can happen later as a separate API refactor.

## 1.7 Final Mental Model

```text
Root menu = capability areas

Documents = document library + admin document actions if admin
Retrieval = query/retrieve/answer flows
Graphs = graph exploration
LightRAG Domains = deployment lifecycle for LightRAG containers
Jobs = indexing job monitor
Observability = audit/query logs
Health / Readiness = system checks
Backend Gaps = planned but unsupported capabilities
```
