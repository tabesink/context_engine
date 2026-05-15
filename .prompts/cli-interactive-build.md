Here is a refined prompt you can run against the uploaded CLI/API docs. I grounded it in the current contract: `ragcli` is intentionally thin, mirrors FastAPI routes, uses stable JSON for automation, keeps backend business rules in the backend, and exposes both supported and planned surfaces explicitly.   Human output can evolve, but JSON is the stable scripting contract. 

````markdown
# Prompt: Architect Screen-Based CLI UX for API-Mirrored Context Engine Capabilities

You are a senior product-minded software architect and CLI UX designer.

## Context

We have a `ragcli` command-line client for a Context Engine backend. The CLI is **not currently a long-running interactive shell**, and it should remain intentionally thin: it authenticates, stores a backend session token, calls FastAPI routes, and renders either human-oriented output or stable JSON.

The CLI is also a **functional test harness for the backend and future frontend**. Each supported CLI command mirrors a backend API route. Each future frontend capability should be traceable back to the same API contract. Therefore, the CLI UX should help us test and reason about the future admin/user frontend without creating a separate product layer or inventing behavior that does not exist in the backend.

Review the uploaded documents:

- `api-contract.md`
- `commands.md`
- `README.md`
- `security-and-output.md`
- `tdd-build-plan.md`

Use them as the source of truth.

## Core Objective

Brainstorm and propose an architecture for a **screen-oriented CLI UX** that organizes the current and planned API capabilities into clear user-facing functionality groups.

Important: “screens” here does **not** necessarily mean a long-running REPL or terminal app. It means a clear UX model for how a user/admin would move through capability groups, see data, execute actions, and test future frontend workflows through the CLI.

The result should help answer:

> How should the CLI organize and render the app’s API capabilities so that it acts as a clean, frontend-aligned testing interface without becoming a high-entropy interactive shell?

## Key Design Constraints

1. The CLI must remain API-first.
   - Real commands call backend routes.
   - Planned commands without backend support must return `not_supported_by_backend`.
   - Do not invent local behavior that bypasses the backend.

2. The CLI should mirror future frontend capabilities.
   - Every screen/functionality group should map to one or more API contracts.
   - The same conceptual grouping should be usable later for a web admin/user dashboard.

3. The CLI should not become unnecessarily complex.
   - Avoid a long-running shell unless there is a strong reason.
   - Prefer composable command groups, optional guided flows, and consistent screen renderers.
   - Keep implementation understandable for a junior developer.

4. Security boundaries must remain backend-owned.
   - The CLI must not infer admin permissions locally.
   - Admin commands should send requests and render backend authorization responses.
   - Never print access tokens, passwords, or sensitive headers.

5. Output contracts must remain stable.
   - `--output json` is the stable automation/scripting contract.
   - Human output can be improved for readability using tables, panels, summaries, and grouped views.

## Current Capability Groups To Analyze

Use the uploaded docs to map the current CLI/API surface into UX groups:

### 1. Session / Identity
Examples:
- `login`
- `logout`
- `auth me`

Think about screens such as:
- Login screen
- Current session screen
- Backend target / saved session screen
- Auth error screen

### 2. Documents / Corpus Exploration
Examples:
- `documents list`
- `documents show`
- `documents structure`
- `documents page`

Think about screens such as:
- Document library
- Document detail
- Document structure/tree
- Page viewer
- Source/evidence viewer

### 3. Retrieval / Question Answering
Examples:
- `documents retrieve`
- `documents answer`
- `query`

Think about screens such as:
- Retrieval test screen
- Answer screen
- Evidence inspection screen
- Debug/admin-only retrieval diagnostics
- Mode comparison screen: `auto`, `semantic`, `navigation`, `hybrid`

### 4. LightRAG Graph Exploration
Examples:
- `lightrag graphs show`
- `lightrag labels list`
- `lightrag labels popular`
- `lightrag labels search`

Think about screens such as:
- Label browser
- Popular labels
- Label search
- Graph neighborhood viewer
- Graph JSON/export view
- Future graph visualization handoff to frontend

### 5. Admin Document Operations
Examples:
- `admin documents upload`
- `admin documents index`
- `admin documents reindex`
- `admin documents delete`
- `admin documents list`

Think about screens such as:
- Admin corpus dashboard
- Upload flow
- Indexing/reindexing flow
- Delete confirmation/output
- Document status dashboard

### 6. Jobs
Examples:
- `jobs list`
- `jobs status`
- `jobs retry`

Think about screens such as:
- Job queue
- Job detail
- Retry flow
- Failed job diagnostics

### 7. Admin Observability
Examples:
- `admin audit-logs list`
- `admin query-logs list`

Think about screens such as:
- Audit log browser
- Query log browser
- User activity/debug view
- Retrieval quality review screen

### 8. Planned / Unsupported Future Surfaces
Examples:
- users
- retrievers
- agents
- conversations
- chat
- messages
- runs
- approvals
- corpus publish/rollback/cleanup

Think about how to represent these in the UX without pretending they work.

## Deliverables

Produce a structured architecture brainstorm with the following sections.

---

## 1. UX Thesis

Explain the recommended CLI UX philosophy.

Address:

- Should this remain a command-based CLI with screen-like renderers?
- Should there be optional guided flows?
- Should there ever be a long-running interactive mode?
- What is the smallest useful UX that tests future frontend behavior without increasing code entropy?

Be opinionated.

---

## 2. Screen Map

Create a screen map that groups capabilities into future frontend-aligned areas.

For each screen, include:

- Screen name
- User role: public, authenticated user, admin
- Purpose
- Backing CLI commands
- Backing API routes
- Primary output components
- JSON contract considerations
- Frontend feature this screen anticipates

Example format:

| Screen | Role | Purpose | CLI Commands | API Routes | Future Frontend Equivalent |
| --- | --- | --- | --- | --- | --- |

---

## 3. Navigation Model

Propose how users should discover and move through functionality without requiring a long-running shell.

Compare options:

### Option A: Pure command groups
Example:
```bash
ragcli documents list
ragcli documents show --document-id DOC_ID
````

### Option B: Screen aliases

Example:

```bash
ragcli screen documents
ragcli screen retrieval
ragcli screen admin
```

### Option C: Guided one-shot flows

Example:

```bash
ragcli admin documents upload-flow --file manual.pdf
ragcli retrieval test --query "reset procedure"
```

### Option D: Optional future TUI/interactive mode

Example:

```bash
ragcli ui
```

Recommend which options to adopt now, later, or avoid.

---

## 4. Proposed Command/Screen Architecture

Propose a lean internal architecture.

Include suggested modules such as:

```text
cli/
  commands/
  screens/
  renderers/
  flows/
  api_client.py
  credentials.py
  errors.py
```

Explain what belongs in each layer.

Important:

* API calls should remain centralized.
* Screen renderers should not contain business logic.
* Guided flows should compose existing command/API behavior.
* JSON output should bypass decorative human rendering.

---

## 5. Human Output Design

Design the human-readable screen patterns.

Include recommendations for:

* Tables
* Detail panels
* Evidence blocks
* Error blocks
* Empty states
* Admin warnings
* Backend disabled-service messages
* `not_supported_by_backend` messages
* Debug sections for admin-only responses

Provide examples of ideal human output for:

1. `documents list`
2. `documents show`
3. `documents retrieve`
4. `query`
5. `lightrag labels popular`
6. `lightrag graphs show`
7. `admin documents upload`
8. `jobs status`
9. `admin query-logs list`
10. Unsupported planned command

---

## 6. JSON Output Contract

Explain how to preserve stable JSON while improving human UX.

Address:

* When JSON should be raw backend response
* When JSON should wrap lists, such as `{ "documents": [...] }`
* How errors should be shaped
* How to avoid breaking scripts
* What behavior tests should lock down

---

## 7. Frontend Traceability Matrix

Create a matrix showing how each CLI capability maps to a future frontend screen.

Example:

| Future Frontend Screen | Current CLI/API Coverage                            | Backend Status | Gaps                           |
| ---------------------- | --------------------------------------------------- | -------------- | ------------------------------ |
| Login                  | `ragcli login`, `/auth/login`                       | supported      | none                           |
| Document Library       | `documents list`, `/documents`                      | supported      | filtering/search maybe missing |
| Retrieval Playground   | `documents retrieve`, `/query/retrieve`             | supported      | compare modes UI               |
| Graph Browser          | `lightrag graphs show`, `/graphs`                   | supported      | visual graph layout            |
| Admin Upload           | `admin documents upload`, `/admin/documents/upload` | supported      | progress events maybe missing  |
| Chat                   | `ragcli chat`                                       | backend gap    | routes needed                  |

---

## 8. Gap Analysis

Identify API/UX gaps that block a clean frontend-like CLI experience.

Separate gaps into:

### Backend gaps

Examples:

* No document range endpoint
* No separate document search endpoint
* No corpus publish/rollback/cleanup endpoint
* Planned chat/conversation/runs/users APIs missing

### CLI UX gaps

Examples:

* Human output too raw
* No consistent screen layout
* No retrieval comparison helper
* No clear admin dashboard summary
* No discoverability command

### Testing gaps

Examples:

* Need behavior tests for new screen renderers
* Need golden JSON tests
* Need error-path tests
* Need admin/non-admin response tests

Prioritize each gap as:

* P0: needed now
* P1: useful soon
* P2: future/frontend polish

---

## 9. Recommended MVP

Define the smallest implementation plan that improves UX without increasing architecture entropy.

The MVP should likely include:

1. Keep existing command groups.
2. Improve human renderers into consistent “screens.”
3. Add a small number of frontend-aligned summary commands if justified.
4. Add guided one-shot flows only where they test real workflows.
5. Keep unsupported planned commands explicit.
6. Preserve JSON behavior.

Give a phased plan:

### Phase 1: Screen renderer cleanup

### Phase 2: Guided workflow helpers

### Phase 3: Frontend traceability docs

### Phase 4: Optional TUI only if truly needed

For each phase, include:

* Goal
* Files/modules likely touched
* Tests required
* Acceptance criteria

---

## 10. Architecture Rules For The Coding Agent

End with clear rules a junior developer or coding agent must follow.

Include rules such as:

* Do not add local business logic to the CLI.
* Do not call LightRAG directly from the CLI.
* Do not print secrets.
* Do not create fake implementations for planned commands.
* Do not break JSON output.
* Keep API route mapping obvious.
* Keep screen rendering separate from API clients.
* Add/modify tests before refactors.
* Prefer simple functions over framework-heavy abstractions.

## Final Output Format

Return the result as a clean architecture brainstorm document with:

1. Executive recommendation
2. Screen map
3. Navigation model
4. Command/screen architecture
5. Human output examples
6. JSON contract rules
7. Frontend traceability matrix
8. Gap analysis
9. MVP implementation plan
10. Coding-agent rules

```

I would run this first as a **planning prompt**, not an implementation prompt. It should produce the screen/UX architecture before asking the coding agent to modify the CLI.
```
