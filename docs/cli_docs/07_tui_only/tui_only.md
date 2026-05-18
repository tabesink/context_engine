# TUI-Only CLI Implementation Plan

Repository: `context_engine`  
Target document path in repo: `docs/cli_docs/07_tui_only/tui_only.md`  
Audience: senior engineer implementing cleanly, with junior engineers able to follow and extend the code  
Design direction: make the interactive terminal UI the only user-facing CLI navigation path

---

## 0. Executive Summary

**Current product:** Operators install `context-engine` / `context-tui` (**`cli.launcher:main`**), which launches the interactive Rich terminal UI backed by **`cli/api_client.py`** plus **`cli/services/`**. Discrete Typer **`context-engine foo bar`** shells are intentionally **removed**—automation stays on REST.

Historical note: Earlier iterations shipped **`ragcli …`** Typer verbs *and* a separate `ragcli ui`; that split increased complexity. Consolidating on **`context-engine` / `context-tui`** aligns repo layout with what `pyproject.toml` registers today.

---

The undesirable **past** shape was duplicated navigation surfaces—command trees plus a parallel menu UI—before TUI-only entry points landed.

---

The sustained target experience:

```text
context-engine
# or
context-tui
```

The backend API should remain unchanged. The TUI calls it through **`ApiClient`**. Business logic continues to belong in FastAPI services, not the terminal layer.

---

## 1. Design Decision

### Decision

Move from a mixed command-mode CLI plus TUI model to a TUI-only user-facing CLI model.

### Keep

```text
FastAPI backend routes
API client layer
credential/token storage
interactive TUI runtime
screen rendering helpers that are still useful
admin/user access separation
backend-driven business rules
```

### Remove or de-publicize

```text
large direct Typer-era subcommand tree (historically named `ragcli`)
planned command stubs that do not call real backend routes
duplicate command-mode UX for documents, retrieval, jobs, admin, and graph features
README sections that present fake `context-engine <subcommand>` shell lines as the main workflow
```

### Replace with

```text
context-engine     -> opens the interactive terminal UI
context-tui        -> alias for the same entry point
```

---

## 2. Target Architecture

```text
┌──────────────────────────────────────────────┐
│ User                                         │
│ Runs: context-engine                         │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│ Interactive Terminal UI                      │
│ cli/tui/*                                    │
│                                              │
│ Responsibilities:                            │
│ - navigation                                 │
│ - forms/prompts                              │
│ - screen rendering                           │
│ - success/error feedback                     │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│ CLI Service Layer / API Client Facade        │
│ cli/services/* or cli/api_client.py          │
│                                              │
│ Responsibilities:                            │
│ - call backend routes                        │
│ - attach auth token                          │
│ - normalize response errors                  │
│ - expose simple methods to TUI screens       │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│ FastAPI Backend                              │
│ app/api/routes/*                             │
│                                              │
│ Responsibilities:                            │
│ - auth rules                                 │
│ - document management                        │
│ - retrieval                                  │
│ - LightRAG proxy                             │
│ - jobs                                       │
│ - audit/query logs                           │
└──────────────────────────────────────────────┘
```

The TUI is a client. The backend remains the source of truth.

---

## 3. Non-Goals

Do not use this refactor to redesign the backend.

Do not move backend business rules into the CLI.

Do not introduce a heavy TUI framework unless the current Rich-based implementation is no longer maintainable.

Do not keep both command-mode and TUI-mode as equal first-class interfaces.

Do not add new API behavior unless required to preserve existing CLI functionality.

---

## 4. Implementation Phases

## Phase 1 — Create a Clean TUI Launcher

### Goal

Create a small entry point that launches the interactive terminal UI directly.

### New file

```text
cli/launcher.py
```

### Responsibilities

`cli/launcher.py` should:

```text
1. Load CLI settings such as backend base URL.
2. Initialize credential/token storage.
3. Create the API client or API client factory.
4. Call the TUI runtime.
5. Exit cleanly on Ctrl+C.
```

### Example shape

```python
# cli/launcher.py

from __future__ import annotations

from cli.config import load_cli_settings
from cli.credentials import CredentialStore
from cli.api_client import ApiClient
from cli.tui.app import run_tui


def main() -> None:
    settings = load_cli_settings()
    credentials = CredentialStore()

    def client_factory() -> ApiClient:
        return ApiClient(
            base_url=settings.api_base_url,
            token=credentials.get_token(),
        )

    run_tui(
        client_factory=client_factory,
        credentials=credentials,
        settings=settings,
    )
```

Use the real existing constructor names from the codebase. This example shows the intended dependency direction, not exact final code.

### Acceptance criteria

```text
[ ] Running context-engine opens the TUI.
[ ] Running context-tui opens the same TUI.
[ ] The launcher contains no business logic.
[ ] The launcher is short enough that a junior developer can understand it quickly.
[ ] Ctrl+C exits cleanly without a traceback.
```

---

## Phase 2 — Update Project Scripts

### Goal

Make the TUI the primary installed command.

### Update `pyproject.toml`

Replace or extend the current script section with:

```toml
[project.scripts]
context-engine = "cli.launcher:main"
context-tui = "cli.launcher:main"
```

### Temporary compatibility option

If you want a safe transition, keep `context-engine` temporarily:

```toml
[project.scripts]
context-engine = "cli.launcher:main"
context-tui = "cli.launcher:main"
context-engine = "cli.deprecated_main:main"
```

Then create:

```text
cli/deprecated_main.py
```

Behavior:

```text
- Print a short deprecation notice.
- Open the TUI.
- Do not expose the old command tree.
```

Example message:

```text
The direct context-engine command interface is deprecated.
Opening the interactive terminal UI instead.
```

### Recommendation

Use the compatibility alias for one release cycle, then remove it.

### Acceptance criteria

```text
[ ] context-engine works after editable install.
[ ] context-tui works after editable install.
[ ] README no longer teaches context-engine subcommands as the main workflow.
[ ] If context-engine remains, it opens the TUI and clearly says it is deprecated.
```

---

## Phase 3 — Inventory Existing Direct CLI Functionality

### Goal

Before deleting command-mode code, verify that no important backend capability is lost.

Use the existing CLI/API surface documentation as the source inventory.

### Current major surfaces to preserve in TUI

```text
Auth/session
- login
- logout
- show current user/session

Documents
- list ready documents
- show document details
- show document structure
- show page text

Retrieval
- retrieve context/evidence
- answer query with sources
- compare retrieval modes, if still useful

Admin documents
- list all documents
- upload document
- index/reindex document
- delete document

Jobs
- list jobs
- view job details
- retry failed job

LightRAG
- list labels
- search labels
- popular labels
- show graph for selected label
- list configured domains
- create domain
- start/stop/recreate domain
- archive remove or permanently delete a domain with confirmation

Observability
- audit logs
- query logs

Health
- basic health
- readiness
```

### Create a preservation table

Add this table to the implementation PR description:

```text
+----------------------+--------------------------+-----------------------+----------------+
| Old CLI Capability   | Existing API Route       | TUI Screen Exists?    | Action Needed  |
+----------------------+--------------------------+-----------------------+----------------+
| Login                | POST /auth/login         | Yes/No                | Fill gap       |
| List documents       | GET /documents           | Yes/No                | Fill gap       |
| Upload document      | POST /admin/.../upload   | Yes/No                | Fill gap       |
| Retry job            | POST /jobs/{id}/retry    | Yes/No                | Fill gap       |
+----------------------+--------------------------+-----------------------+----------------+
```

### Acceptance criteria

```text
[ ] Every useful old command has a TUI equivalent or a documented reason for removal.
[ ] Planned stub commands are not treated as required features.
[ ] Admin-only features are clearly marked in the TUI.
[ ] User-level features remain accessible to non-admin users.
```

---

## Phase 4 — Add or Complete Missing TUI Screens

### Goal

Make the TUI complete enough to replace direct command-mode usage.

### Main menu target

```text
┌──────────────────────────────────────────────────────────────┐
│ Context Engine Terminal                                      │
│ User: admin@example.com                         Role: Admin  │
├──────────────────────────────────────────────────────────────┤
│ Navigate backend surfaces                                    │
│                                                              │
│  [1] Documents                                               │
│  [2] Retrieval / Ask                                         │
│  [3] LightRAG Graphs                                         │
│  [4] Admin Documents                         Admin only      │
│  [5] Jobs                                    Admin only      │
│  [6] Observability                           Admin only      │
│  [7] Health / Readiness                                      │
│  [8] Session                                                 │
│  [9] Logout                                                  │
│  [Q] Quit                                                    │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ Controls: ↑/↓ Move   Enter Select   Esc Back   Q Quit        │
└──────────────────────────────────────────────────────────────┘
```

### Screen design rules

Each screen should follow this structure:

```text
Title
Session/role context
Short explanation
Available actions
Result table or response panel
Keyboard controls
Error message area
```

### Example: documents screen

```text
┌──────────────────────────────────────────────────────────────┐
│ Documents                                                    │
│ User: user@example.com                          Role: User   │
├──────────────────────────────────────────────────────────────┤
│ API surface                                                  │
│                                                              │
│  [1] List ready documents       GET /documents               │
│  [2] View document details      GET /documents/{id}          │
│  [3] View structure             GET /documents/{id}/structure│
│  [4] View page text             GET /documents/{id}/pages/{n}│
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ Controls: ↑/↓ Move   Enter Select   Esc Back   Q Quit        │
└──────────────────────────────────────────────────────────────┘
```

### Example: admin documents screen

```text
┌──────────────────────────────────────────────────────────────┐
│ Admin Documents                                              │
│ User: admin@example.com                         Role: Admin  │
├──────────────────────────────────────────────────────────────┤
│ Admin-only actions                                           │
│                                                              │
│  [1] List all documents        GET    /admin/documents       │
│  [2] Upload document           POST   /admin/documents/upload│
│  [3] Index document            POST   /admin/documents/{id}/index│
│  [4] Delete document           DELETE /admin/documents/{id}  │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ Warning: destructive actions require confirmation.           │
│ Controls: ↑/↓ Move   Enter Select   Esc Back   Q Quit        │
└──────────────────────────────────────────────────────────────┘
```

### Acceptance criteria

```text
[ ] Each major API surface has a TUI screen.
[ ] Each screen has a clear title and controls.
[ ] Admin-only actions are visibly marked.
[ ] Destructive actions require confirmation.
[ ] Backend errors are shown in plain language.
[ ] Raw tracebacks are not shown to users.
```

---

## Phase 5 — Extract Direct Command Logic into Services

### Goal

Avoid deleting useful logic trapped inside `cli/main.py`.

Move reusable API-calling logic into small service modules before removing command handlers.

### Recommended structure

```text
cli/
  launcher.py
  api_client.py
  credentials.py
  config.py
  services/
    __init__.py
    auth.py
    documents.py
    admin_documents.py
    retrieval.py
    jobs.py
    lightrag.py
    lightrag_domains.py
    observability.py
    health.py
  tui/
    app.py
    screens/
      login.py
      main_menu.py
      documents.py
      retrieval.py
      admin_documents.py
      jobs.py
      lightrag.py
      observability.py
      health.py
      session.py
```

### Service module example

```python
# cli/services/documents.py

from __future__ import annotations

from cli.api_client import ApiClient


class DocumentService:
    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list_documents(self) -> list[dict]:
        return self._client.get("/documents")

    def get_document(self, document_id: str) -> dict:
        return self._client.get(f"/documents/{document_id}")

    def get_structure(self, document_id: str) -> dict:
        return self._client.get(f"/documents/{document_id}/structure")

    def get_page(self, document_id: str, page_number: int) -> dict:
        return self._client.get(f"/documents/{document_id}/pages/{page_number}")
```

This keeps screens readable:

```python
service = DocumentService(client)
documents = service.list_documents()
render_documents_table(documents)
```

### Acceptance criteria

```text
[ ] TUI screens do not build raw URLs everywhere.
[ ] API route paths are centralized in service methods or a route constants module.
[ ] Service methods have simple names junior developers can understand.
[ ] Services do not contain terminal rendering code.
[ ] Screens do not contain backend business rules.
```

---

## Phase 6 — Retire the Direct `context-engine` Command Tree

### Goal

Remove duplicate user-facing command-mode navigation.

### Options

#### Option A — Soft retirement, recommended first

```text
Keep cli/main.py small.
Remove subcommands.
Make it open the TUI.
Print deprecation message if invoked as context-engine.
```

#### Option B — Hard removal

```text
Delete command-mode CLI handlers.
Remove context-engine from pyproject.toml.
Only expose context-engine and context-tui.
```

### Recommended sequence

```text
1. Soft retire first.
2. Update docs and tests.
3. Confirm no internal workflows depend on context-engine subcommands.
4. Hard remove in a later cleanup PR.
```

### Acceptance criteria

```text
[ ] No user docs depend on direct context-engine subcommands.
[ ] The TUI exposes all retained functionality.
[ ] Old command-mode tests are removed or rewritten.
[ ] Import paths are clean after command handlers are removed.
```

---

## Phase 7 — Testing Plan

### Unit tests

Test service modules without rendering the terminal.

```text
cli/services/documents.py
cli/services/admin_documents.py
cli/services/retrieval.py
cli/services/jobs.py
cli/services/lightrag.py
cli/services/health.py
```

Test cases:

```text
[ ] correct HTTP method is used
[ ] correct route path is used
[ ] auth token is attached by client layer
[ ] 401/403 errors produce friendly error objects
[ ] validation errors are passed to screens cleanly
```

### TUI screen tests

Keep these lightweight.

```text
[ ] unauthenticated user sees login screen
[ ] authenticated user sees main menu
[ ] admin sees admin screens
[ ] non-admin does not see or cannot execute admin actions
[ ] failed API call renders friendly error message
[ ] destructive action requires confirmation
```

### Smoke tests

```text
[ ] context-engine --help does not crash, if supported
[ ] context-engine opens TUI
[ ] context-tui opens TUI
[ ] context-engine opens TUI with deprecation notice, if compatibility alias is kept
```

### Manual QA script

```text
1. Start backend locally.
2. Install CLI in editable mode.
3. Run context-engine.
4. Login as normal user.
5. Confirm user can list documents and run retrieval.
6. Confirm user cannot access admin document upload/delete.
7. Logout.
8. Login as admin.
9. Upload a document.
10. Confirm indexing job appears.
11. View job status.
12. View LightRAG labels/graph if LightRAG is configured.
13. View LightRAG Domains as admin and exercise create/start/stop/recreate/remove against a test domain when `LIGHTRAG_DEPLOY_ENABLED=true`.
14. View audit/query logs.
15. Quit cleanly.
```

---

## Phase 8 — Documentation Updates

### Update README

Replace command-mode examples like:

```bash
context-engine documents list
context-engine query "What is this document about?"
```

with:

```bash
context-engine
```

Then show the flow:

```text
Login -> Main Menu -> Documents / Retrieval / Admin / Jobs / Graphs
```

### Add new docs

```text
docs/TUI_ONLY_CLI_IMPLEMENTATION_PLAN.md
docs/TUI_NAVIGATION_GUIDE.md
docs/CLI_API_SURFACE_ASCII_SCREENS.md    # existing/generated doc can be updated
```

### README section example

```markdown
## Terminal Application

The recommended way to use the local CLI is through the interactive terminal UI:

```bash
context-engine
```

The terminal UI calls the FastAPI backend and exposes document search, retrieval, admin upload/indexing, job status, LightRAG graph views, and observability screens.

Direct `context-engine ...` subcommands are deprecated. Use the interactive terminal UI instead.
```

### Acceptance criteria

```text
[ ] README presents the TUI as the primary CLI.
[ ] Direct command-mode examples are removed or marked deprecated.
[ ] Junior developers can find the launcher, service layer, and screens quickly.
[ ] The implementation plan is committed under docs/.
```

---

## 9. Pull Request Breakdown

Avoid one huge refactor PR. Use a small series of easy-to-review PRs.

### PR 1 — Add TUI launcher

```text
- Add cli/launcher.py
- Add context-engine and context-tui scripts
- Keep old context-engine unchanged for now
- Add smoke test for launcher
```

### PR 2 — Add service layer

```text
- Extract API-calling logic from direct command handlers
- Add cli/services/*
- Point TUI screens to services where appropriate
- Add unit tests for service methods
```

### PR 3 — Complete TUI screen coverage

```text
- Add missing screens
- Add admin-only checks in navigation
- Add friendly error panels
- Add confirmation prompts for destructive actions
```

### PR 4 — Soft deprecate direct context-engine commands

```text
- Change context-engine to open TUI with deprecation message
- Remove direct command docs from README
- Update tests
```

### PR 5 — Hard cleanup

```text
- Delete old command handlers if no longer needed
- Delete planned unsupported command stubs
- Simplify imports
- Final documentation cleanup
```

---

## 10. Code Quality Rules for This Refactor

### Rule 1 — Keep dependency direction simple

```text
TUI screens -> services -> API client -> FastAPI backend
```

Do not let lower layers import TUI code.

### Rule 2 — Keep screens thin

Screens should handle:

```text
input
navigation
rendering
calling one service method at a time
```

Screens should not handle:

```text
backend permissions
retrieval algorithms
document indexing logic
database rules
LightRAG internals
```

### Rule 3 — Keep services boring

Service methods should look obvious:

```python
jobs.retry(job_id)
documents.get_page(document_id, page_number)
admin_documents.upload(path)
lightrag.search_labels(query)
```

### Rule 4 — Prefer explicit names

Good:

```text
AdminDocumentService
RetrievalService
LightRagGraphService
render_admin_documents_screen
confirm_delete_document
```

Avoid:

```text
Manager
Handler
Processor
Utils
Thing
run_action
```

### Rule 5 — Fail clearly

Bad terminal error:

```text
Exception: 403 Client Error
```

Good terminal error:

```text
Permission denied.
Only admin users can upload documents.
```

---

## 11. Risks and Mitigations

```text
+----------------------------------------+-----------------------------------------------+
| Risk                                   | Mitigation                                    |
+----------------------------------------+-----------------------------------------------+
| Existing scripts depend on context-engine      | Keep temporary compatibility alias            |
| TUI lacks feature parity               | Complete preservation table before deletion   |
| Large refactor becomes hard to review  | Split into small PRs                          |
| Business logic leaks into TUI          | Keep service/API/backend boundaries clear     |
| Admin actions become too easy to run   | Require confirmations and mark admin screens  |
| Junior devs cannot follow structure    | Use explicit names and small modules          |
+----------------------------------------+-----------------------------------------------+
```

---

## 12. Final Target User Experience

### Start

```bash
context-engine
```

### Login

```text
┌──────────────────────────────────────────────────────────────┐
│ Context Engine Terminal                                      │
│ Login                                                        │
├──────────────────────────────────────────────────────────────┤
│ Email:    admin@example.com                                  │
│ Password: ********                                           │
│                                                              │
│ [Enter] Login     [Esc] Quit                                 │
└──────────────────────────────────────────────────────────────┘
```

### Navigate

```text
┌──────────────────────────────────────────────────────────────┐
│ Context Engine Terminal                                      │
│ User: admin@example.com                         Role: Admin  │
├──────────────────────────────────────────────────────────────┤
│  > Documents                                                 │
│    Retrieval / Ask                                           │
│    LightRAG Graphs                                           │
│    Admin Documents                                           │
│    Jobs                                                      │
│    Observability                                             │
│    Health / Readiness                                        │
│    Logout                                                    │
│    Quit                                                      │
├──────────────────────────────────────────────────────────────┤
│ Controls: ↑/↓ Move   Enter Select   Esc Back   Q Quit        │
└──────────────────────────────────────────────────────────────┘
```

The user should not need to memorize backend routes or command syntax. The TUI becomes the discoverable navigation layer for the backend.

---

## 13. Definition of Done

This design change is complete when:

```text
[ ] `context-engine` launches the TUI directly.
[ ] `context-tui` launches the TUI directly.
[ ] Direct `context-engine ...` command-mode navigation is removed or deprecated.
[ ] The TUI covers all retained backend API surfaces.
[ ] Admin-only actions are protected and clearly labeled.
[ ] The backend API is unchanged except for any explicitly approved gap-filling routes.
[ ] CLI service modules are small, readable, and tested.
[ ] README and docs describe the TUI-only workflow.
[ ] Junior engineers can add a new TUI screen by following an existing screen + service pattern.
```

---

## 14. Recommended Next Coding-Agent Prompt

```markdown
# Task: Refactor Context Engine CLI to TUI-Only Navigation

You are a senior software engineer refactoring the `context_engine` repository.

## Goal

Make the interactive terminal UI the only user-facing CLI navigation path.

Users should run:

```bash
context-engine
```

or:

```bash
context-tui
```

The old direct `context-engine ...` command tree should be removed or temporarily turned into a compatibility alias that opens the TUI with a deprecation notice.

## Constraints

- Do not change backend API behavior.
- Do not move business logic into the TUI.
- Keep code lightweight and junior-dev friendly.
- Preserve all useful existing CLI functionality inside TUI screens.
- Remove planned stubs that do not call real backend routes unless they are intentionally documented as gaps.

## Implementation Steps

1. Add `cli/launcher.py` that directly launches the TUI.
2. Update `pyproject.toml` scripts to expose `context-engine` and `context-tui`.
3. Inventory old `context-engine` command capabilities and map each useful capability to a TUI screen.
4. Extract reusable API-calling logic from command handlers into small `cli/services/*` modules.
5. Update or add TUI screens for documents, retrieval, admin documents, jobs, LightRAG graphs, observability, health, and session.
6. Soft-deprecate or remove the old `context-engine` command tree.
7. Update README and docs.
8. Add tests for the launcher, service methods, and key TUI access rules.

## Code Style

Write clean, explicit, boring code that a junior engineer can follow.

Prefer:

- small files
- clear names
- direct control flow
- simple service classes
- friendly terminal errors

Avoid:

- clever abstractions
- duplicate command paths
- hidden business logic in screen code
- large unreviewable PRs
```
