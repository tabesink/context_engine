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


---

# 2. Target Menu and Screen Flows

## 2.1 Target Root Menu

```text
CONTEXT ENGINE

Backend: http://127.0.0.1:8010
Session: admin@example.com

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

For normal users:

```text
CONTEXT ENGINE

Backend: http://127.0.0.1:8010
Session: user@example.com

> Documents
  Retrieval
  Graphs
  Health / Readiness
  Logout
  Quit
```

Optional: keep `Backend Gaps` visible only in development mode.

## 2.2 Documents Screen

```text
DOCUMENTS

> Browse Ready Documents
  Search / Filter Documents
  View Document Detail
  View Structure / Outline
  View Page
  Admin Actions
  Back
```

If user is not admin:

```text
DOCUMENTS

> Browse Ready Documents
  Search / Filter Documents
  View Document Detail
  View Structure / Outline
  View Page
  Back
```

If search endpoint is still a backend gap, show:

```text
Search / Filter Documents  [backend gap]
```

or hide it until implemented.

## 2.3 Documents Admin Actions Screen

```text
DOCUMENTS > ADMIN ACTIONS

> Upload Document
  List All Documents
  Reingest / Refresh Status Document
  Delete Document
  Back
```

No top-level `Admin Documents`.

## 2.4 Retrieval Screen

```text
RETRIEVAL

> Retrieval Preview
  Citation Answer
  Compare Modes
  Domain Selector
  Back
```

Domain selector calls:

```text
GET /lightrag/domains
```

and query payloads include:

```json
{
  "lightrag_domain_id": "fatigue"
}
```

when selected.

## 2.5 Graphs Screen

```text
GRAPHS

> Graph Summary
  Label Catalog
  Popular Labels
  Search Labels
  Back
```

API calls stay the same initially:

```text
GET /graphs
GET /graph/label/list
GET /graph/label/popular
GET /graph/label/search
```

The label is changed only in the UI.

## 2.6 LightRAG Domains Screen

```text
LIGHTRAG DOMAINS

> List Domains
  Create Domain
  Show Domain Detail
  Start Domain
  Stop Domain
  Recreate Domain
  Regenerate Domain Files
  Archive Remove Domain
  Permanent Delete Domain
  Back
```

All items are admin-only. The root menu may hide `LightRAG Domains` for non-admin users, or show it and let backend return `403`. Preferred for usability: hide for non-admin users.

## 2.7 Jobs Screen

```text
JOBS

> List Jobs
  Show Job Detail
  Retry Failed Job
  Back
```

## 2.8 Observability Screen

```text
OBSERVABILITY

> Audit Logs
  Query Logs
  Back
```

If later merged into `/admin/logs?type=...`, keep the screen unchanged and only update the service helper.

## 2.9 Health / Readiness Screen

```text
HEALTH / READINESS

> API Health
  Readiness
  Storage Status
  Worker / Redis Status
  LightRAG Runtime Status
  LightRAG Deploy Status
  Back
```

Only show checks that are backed by real routes. Do not fake system status.

## 2.10 Backend Gaps Screen

```text
BACKEND GAPS

The following screens are planned but do not have backend support yet:

- Conversations
- Chat history
- Users
- Agents
- Corpus publish / rollback
- Runs / approvals

Back
```

This prevents fake success and makes gaps explicit.


---

# 3. Documents vs Admin Documents

## 3.1 Why Both Exist Today

The backend has two different document surfaces.

### User document surface

```text
GET /documents
GET /documents/{document_id}
GET /documents/{document_id}/structure
GET /documents/{document_id}/pages/{page_number}
```

Purpose:

- authenticated users browse ready documents
- users inspect document metadata
- users view structure/outline
- users inspect page content

This is the normal document library.

### Admin document surface

```text
GET    /admin/documents
POST   /admin/documents/upload
POST   /admin/documents/{id}/reingest
POST   /admin/documents/{id}/refresh-status
DELETE /admin/documents/{id}
```

Purpose:

- admins upload documents
- admins list all documents, not only ready documents
- admins reingest/refresh-status
- admins delete/soft-delete
- admins see failed/indexing/deleted states

So the backend split is valid.

## 3.2 Why It Feels Redundant in the TUI

The root labels:

```text
Documents
Admin Documents
```

make users ask:

```text
Why are there two document screens?
```

The better root-level concept is one `Documents` area with role-aware actions.

## 3.3 Recommended UI Structure

```text
Documents
  ├── Browse Ready Documents       -> GET /documents
  ├── View Detail                  -> GET /documents/{id}
  ├── View Structure               -> GET /documents/{id}/structure
  ├── View Page                    -> GET /documents/{id}/pages/{page}
  └── Admin Actions                -> admin-only
        ├── Upload                 -> POST /admin/documents/upload
        ├── List All               -> GET /admin/documents
        ├── Reingest               -> POST /admin/documents/{id}/reingest
        ├── Refresh Status         -> POST /admin/documents/{id}/refresh-status
        └── Delete                 -> DELETE /admin/documents/{id}
```

## 3.4 Should Backend Routes Be Merged?

Not now.

Keep existing routes for stability.

Later, optional API simplification could become:

```text
GET /documents?scope=ready
GET /documents?scope=all       # admin-only when scope=all
```

But this is a backend API refactor, not necessary for the TUI cleanup.

## 3.5 Recommended Naming If Kept Separate Temporarily

If you do not fold it immediately, use clearer names:

| Old | Better |
|---|---|
| `Documents` | `Document Library` |
| `Admin Documents` | `Document Admin` |

But the best version is still one `Documents` menu with admin actions nested inside.


---

# 4. LightRAG Domains Screen Plan

## 4.1 Goal

Move all LightRAG domain deployment CRUD out of the root menu and into the `LightRAG Domains` screen.

Root menu should contain only:

```text
LightRAG Domains
```

not:

```text
LightRAG Domains
Create LightRAG Domain
Start LightRAG Domain
Stop LightRAG Domain
Recreate LightRAG Domain
Remove LightRAG Domain
```

## 4.2 Backend Contract

Use existing domain lifecycle routes:

| UI action | Backend route |
|---|---|
| Retrieval domain picker | `GET /lightrag/domains` |
| List configured domains | `GET /admin/lightrag/domains` |
| Create domain | `POST /admin/lightrag/domains` |
| Show domain detail | `GET /admin/lightrag/domains/{domain_id}` |
| Start domain | `POST /admin/lightrag/domains/{domain_id}/up` |
| Stop domain | `POST /admin/lightrag/domains/{domain_id}/down` |
| Recreate domain | `POST /admin/lightrag/domains/{domain_id}/recreate` |
| Regenerate domain files | `POST /admin/lightrag/domains/{domain_id}/regenerate` |
| Archive remove | `DELETE /admin/lightrag/domains/{domain_id}` |
| Permanent delete | `DELETE /admin/lightrag/domains/{domain_id}?permanent=true` |

## 4.3 Screen Layout

```text
LIGHTRAG DOMAINS

Configured domains:

+----------+--------------+------+----------+----------+----------------+
| Domain   | Display Name | Port | Runtime  | Health   | Default        |
+----------+--------------+------+----------+----------+----------------+
| fatigue  | Fatigue Docs | 9622 | running  | healthy  | yes            |
| abaqus   | Abaqus Docs  | 9623 | stopped  | unknown  | no             |
+----------+--------------+------+----------+----------+----------------+

Actions:
> Create Domain
  Show Domain Detail
  Start Domain
  Stop Domain
  Recreate Domain
  Regenerate Domain Files
  Archive Remove Domain
  Permanent Delete Domain
  Back
```

## 4.4 Create Domain Form

```text
CREATE LIGHTRAG DOMAIN

Domain ID:       fatigue
Display name:    Fatigue Manuals
Host port:       9622  (blank = auto)
Make default:    yes/no

Submit / Cancel
```

Request body:

```json
{
  "domain_id": "fatigue",
  "display_name": "Fatigue Manuals",
  "host_port": 9622,
  "make_default": true
}
```

## 4.5 Start / Stop / Recreate

These flows should use a select-domain first pattern:

```text
START LIGHTRAG DOMAIN

Select domain:
> fatigue    stopped    port 9622
  abaqus     running    port 9623

Confirm start selected domain? yes/no
```

## 4.6 Remove Domain

Default is archive:

```text
ARCHIVE REMOVE LIGHTRAG DOMAIN

Domain: fatigue

This will:
- stop the domain container if running
- remove it from active domain manifest
- move .data/lightrag/domains/fatigue to .data/lightrag/deleted/fatigue-<timestamp>

Type ARCHIVE fatigue to continue:
```

Permanent delete:

```text
PERMANENT DELETE LIGHTRAG DOMAIN

Domain: fatigue

This permanently deletes domain data.
This is only allowed when LIGHTRAG_ALLOW_PERMANENT_DELETE=true.

Type DELETE fatigue to continue:
```

## 4.7 Service Layer

Add or update:

```text
cli/services/lightrag_domains.py
```

This file should call backend routes through `ApiClient`.

It must not:

- call Docker
- edit `.data`
- generate env files
- call LightRAG directly

## 4.8 TUI Screen Files

Likely files:

```text
cli/tui/screens/lightrag_domains.py
cli/tui/renderers/lightrag_domains.py
```

or equivalent names matching current project structure.

## 4.9 Tests

Add/update tests:

```text
tests/test_cli_tui.py
tests/test_cli_services.py
tests/test_cli_screen_renderers.py
```

Required assertions:

- Root menu includes only one `LightRAG Domains` item.
- Root menu does not include Create/Start/Stop/Recreate/Remove LightRAG Domain.
- LightRAG Domains screen contains create/start/stop/recreate/remove actions.
- TUI service methods call the correct admin routes.
- Permanent delete requires typed confirmation.


---

# 5. Rename LightRAG Graphs to Graphs

## 5.1 Decision

Rename the TUI menu label:

```text
LightRAG Graphs
```

to:

```text
Graphs
```

## 5.2 Why

`LightRAG Graphs` leaks implementation details into the operator-facing root menu.

The backend may currently proxy to LightRAG, but the user-facing capability is graph exploration.

## 5.3 Backend Routes Stay the Same Initially

Do not change backend routes as part of this UI cleanup.

Current supported graph routes:

```text
GET /graphs
GET /graph/label/list
GET /graph/label/popular
GET /graph/label/search
```

## 5.4 TUI Screen

Old:

```text
LIGHTRAG GRAPHS
```

New:

```text
GRAPHS
```

Optional subtitle:

```text
Remote graph data from the selected LightRAG domain
```

## 5.5 Future Backend Simplification

Later, the graph API can be cleaned up:

```text
GET /graph
GET /graph/labels?q=&sort=popular&limit=...
```

But do not bundle that with this menu cleanup.

## 5.6 Tests

Update tests that assert screen labels:

- root menu contains `Graphs`
- root menu does not contain `LightRAG Graphs`
- graph screen still calls the same backend routes
- disabled LightRAG still renders backend error unchanged


---

# 6. TDD Implementation Plan

## Slice 1: Root Menu Cleanup

### Test first

Add/update tests:

```text
tests/test_cli_tui.py
tests/test_cli_screen_renderers.py
```

Assertions:

```text
root menu includes Documents
root menu includes Retrieval
root menu includes Graphs
root menu includes LightRAG Domains
root menu does not include LightRAG Graphs
root menu does not include Admin Documents
root menu does not include Create LightRAG Domain
root menu does not include Start LightRAG Domain
root menu does not include Stop LightRAG Domain
root menu does not include Recreate LightRAG Domain
root menu does not include Remove LightRAG Domain
```

### Implement

Update the root menu builder under `cli/tui/`.

## Slice 2: LightRAG Domains Nested Actions

### Test first

Assertions:

```text
LightRAG Domains screen includes Create Domain
LightRAG Domains screen includes Start Domain
LightRAG Domains screen includes Stop Domain
LightRAG Domains screen includes Recreate Domain
LightRAG Domains screen includes Regenerate Domain Files
LightRAG Domains screen includes Archive Remove Domain
LightRAG Domains screen includes Permanent Delete Domain
```

### Implement

Move existing action entries into `LightRAG Domains` screen.

No backend changes needed.

## Slice 3: Rename LightRAG Graphs to Graphs

### Test first

Assertions:

```text
root menu shows Graphs
graph screen title is GRAPHS
graph service still calls GET /graphs and /graph/label/...
```

### Implement

Change UI label only.

No backend changes needed.

## Slice 4: Documents Menu Consolidation

### Test first

Assertions:

```text
root menu shows Documents
root menu does not show Admin Documents
Documents screen shows Admin Actions for admin users
Documents screen hides Admin Actions for normal users, or renders disabled with backend-auth explanation
Admin Actions screen calls /admin/documents routes
Browse Documents calls /documents routes
```

### Implement

Move admin document actions under the Documents screen.

No backend route merge required.

## Slice 5: Documentation Update

Update:

```text
docs/cli_docs/tui_ux.md
docs/cli_docs/frontend_traceability.md
docs/cli_docs/commands.md
docs/cli_docs/api-contract.md
```

Make sure docs say:

- `context-engine` and `context-tui` are the supported entrypoints.
- Root menu is capability areas only.
- LightRAG domain CRUD lives under `LightRAG Domains`.
- `Graphs` is the operator-facing graph screen.
- `Documents` contains admin actions when user is admin.

## Slice 6: Conformance Tests

Run:

```bash
pytest tests/test_cli_tui.py tests/test_cli_screen_renderers.py tests/test_cli_services.py -q
```

If ASCII conformance tests exist:

```bash
pytest tests/test_cli_ascii_samples.py -q
```

## Slice 7: Optional Backend Route Simplification Later

Do not do this now unless explicitly scoped.

Potential future simplifications:

| Current | Future |
|---|---|
| `/query/answer` + `/query` | Keep one public answer endpoint |
| `/admin/documents/{id}/reingest` + `/refresh-status` | `POST /admin/documents/{id}/reingest` |
| `/graph/label/list`, `/popular`, `/search` | `GET /graph/labels?q=&sort=&limit=` |
| `/admin/documents` + `/documents` | maybe `GET /documents?scope=all`, admin-only |


---

# 7. Coding Agent Prompt

Copy this prompt into your coding agent.

```markdown
# Task: Clean Up Context Engine TUI Menu and Nest LightRAG Domain CRUD

You are a senior software engineer. Make the terminal UI cleaner and lower entropy while preserving the existing backend API contract.

## Current Problem

After login, the TUI root menu currently shows:

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

This is too flat and redundant.

## Required New Root Menu

Change the root menu to capability areas only:

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

For non-admin users, hide admin-only areas where the current TUI role model supports that.

## Required Changes

### 1. Move LightRAG domain CRUD inside LightRAG Domains

Remove these from root:

```text
Create LightRAG Domain
Start LightRAG Domain
Stop LightRAG Domain
Recreate LightRAG Domain
Remove LightRAG Domain
```

Add them inside the `LightRAG Domains` screen:

```text
LightRAG Domains
  ├── List Domains
  ├── Create Domain
  ├── Show Domain Detail
  ├── Start Domain
  ├── Stop Domain
  ├── Recreate Domain
  ├── Regenerate Domain Files
  ├── Archive Remove Domain
  └── Permanent Delete Domain
```

Use existing backend routes:

```text
GET    /admin/lightrag/domains
POST   /admin/lightrag/domains
GET    /admin/lightrag/domains/{domain_id}
POST   /admin/lightrag/domains/{domain_id}/up
POST   /admin/lightrag/domains/{domain_id}/down
POST   /admin/lightrag/domains/{domain_id}/recreate
POST   /admin/lightrag/domains/{domain_id}/regenerate
DELETE /admin/lightrag/domains/{domain_id}
DELETE /admin/lightrag/domains/{domain_id}?permanent=true
```

Do not call Docker from TUI. TUI calls `cli/services/lightrag_domains.py`, which calls backend API through `ApiClient`.

### 2. Rename LightRAG Graphs to Graphs

Change only the TUI label:

```text
LightRAG Graphs -> Graphs
```

Do not rename backend routes in this task.

Keep using:

```text
GET /graphs
GET /graph/label/list
GET /graph/label/popular
GET /graph/label/search
```

### 3. Fold Admin Documents into Documents

Remove top-level:

```text
Admin Documents
```

Inside `Documents`, add admin-only actions:

```text
Documents
  ├── Browse Ready Documents
  ├── View Document Detail
  ├── View Structure / Outline
  ├── View Page
  └── Admin Actions
        ├── Upload Document
        ├── List All Documents
        ├── Reingest / Refresh Status Document
        └── Delete Document
```

Keep backend routes unchanged:

```text
GET /documents
GET /documents/{id}
GET /documents/{id}/structure
GET /documents/{id}/pages/{page}
POST /admin/documents/upload
GET /admin/documents
POST /admin/documents/{id}/reingest
POST /admin/documents/{id}/refresh-status
DELETE /admin/documents/{id}
```

This is UI consolidation only, not a backend route merge.

## Architectural Rules

- `context-engine` and `context-tui` remain the supported entrypoints.
- `cli/main.py` remains a compatibility delegate only.
- Use `cli/launcher.py`, `cli/services/`, and `cli/tui/`.
- TUI screens must not contain backend business logic.
- TUI screens must not call LightRAG directly.
- TUI screens must not call Docker directly.
- Backend authorization remains the source of truth.
- Planned backend gaps must render as gaps, not fake success.

## Tests First

Update or add tests before implementation:

1. Root menu contains `Graphs`, not `LightRAG Graphs`.
2. Root menu contains one `LightRAG Domains` item.
3. Root menu does not contain LightRAG domain CRUD actions.
4. LightRAG Domains screen contains domain CRUD actions.
5. Root menu contains `Documents`, not `Admin Documents`.
6. Documents screen contains admin actions for admin users.
7. Documents screen hides or disables admin actions for normal users.
8. Graph screen still calls existing graph routes.
9. LightRAG domain actions still call existing admin domain routes through `cli/services`.

Run:

```bash
pytest tests/test_cli_tui.py tests/test_cli_screen_renderers.py tests/test_cli_services.py -q
```

If available:

```bash
pytest tests/test_cli_ascii_samples.py -q
```

## Documentation Updates

Update:

```text
docs/cli_docs/tui_ux.md
docs/cli_docs/frontend_traceability.md
docs/cli_docs/commands.md
docs/cli_docs/api-contract.md
```

Make the docs match the new screen hierarchy.

## Acceptance Criteria

The task is complete when:

1. Root menu is shorter and capability-based.
2. LightRAG CRUD is nested under `LightRAG Domains`.
3. `LightRAG Graphs` is renamed to `Graphs`.
4. `Admin Documents` is no longer a top-level duplicate.
5. Admin document actions remain available under `Documents`.
6. Backend routes are not broken or unnecessarily renamed.
7. TUI services still call backend APIs through `ApiClient`.
8. Tests prove the new menu structure.
```
