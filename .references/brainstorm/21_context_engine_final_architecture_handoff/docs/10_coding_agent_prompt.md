# 10 — Coding Agent Prompt

Use this prompt with a coding agent.

```markdown
You are working on the `v1` branch of:

https://github.com/tabesink/context_engine/tree/v1

Act as a senior full-stack engineer. Implement the lean final architecture refactor in small, safe phases. Do not make large destructive changes. Preserve current behavior while migrating the app toward clearer ownership boundaries.

## Final Architecture Rule

Documents own uploaded files and local structure.
Domains own LightRAG runtime/workspace identity.
Operations own all async/global visibility.
`processing-status` is the only document status API.
Provider config is env/domain-level unless runtime admin editing is explicitly retained.
Frontend talks to one typed API layer.

## Required Phases

### Phase 0 — Baseline

Create `docs/ARCHITECTURE_CURRENT.md` with:

- backend route inventory
- frontend endpoint callers
- database model inventory
- current document upload flow
- current retrieval flow
- current domain lifecycle flow
- current provider settings flow

Do not change runtime behavior in this phase.

### Phase 1 — Document Status

Make `processing-status` the canonical status API.

- Migrate frontend away from `ingestion-status`.
- Keep `ingestion-status` backend routes as deprecated wrappers temporarily.
- Add tests proving `processing-status` works for user/admin flows.

### Phase 2 — Operations

Make `/operations` the frontend/admin async visibility API.

- Keep the internal `jobs` table if needed.
- Make document ingestion and domain lifecycle actions visible as operations.
- Stop normal frontend flows from using `/jobs`.
- Keep `/jobs` only as debug/deprecated if necessary.

### Phase 3 — LightRAG Domain Lifecycle

Simplify visible lifecycle actions to:

- create
- start
- stop
- delete

Remove from normal UI:

- repair
- recreate
- regenerate
- purge
- upload document from domain More menu
- view documents from domain More menu
- view logs from domain More menu

Document source-of-truth rules:

- DB domain row = desired metadata/state
- Docker/LightRAG health = observed runtime state
- manifest/domain.env = generated artifact
- operations = lifecycle transition visibility
- audit logs = actor/action accountability

### Phase 4 — Provider Config

Clarify provider source of truth.

Preferred lean target:

- `.env` / `domain.env` owns provider config
- provider UI is diagnostics-first
- retrieval defaults are not runtime-editable
- embedding model is fixed per domain
- no secrets are returned to frontend

### Phase 5 — Upload Workflow

Expose these stages consistently:

- `register_upload`
- `parse_local_structure`
- `push_to_lightrag`
- `poll_remote_indexing`
- `complete`
- `failed`

Upload response should include:

- document id
- operation id
- processing status URL

### Phase 6 — Frontend API Layer

Centralize backend calls in:

`client/src/lib/api/*`

Components should not hardcode backend endpoint URLs.

### Phase 7 — Database Guardrails

Do not drop tables immediately.

Classify tables as:

- core
- optional
- deprecated candidate

Remove code usage before migrations.

### Phase 8 — Tests and Docs

Add/update docs:

- `docs/ARCHITECTURE_TARGET.md`
- `docs/API_CONTRACTS.md`
- `docs/DOMAIN_LIFECYCLE.md`
- `docs/DOCUMENT_UPLOAD_WORKFLOW.md`
- `docs/OPERATIONS_VISIBILITY.md`
- `docs/PROVIDER_CONFIG.md`

Add tests for:

- auth/role gating
- upload
- processing-status
- operations
- domain lifecycle
- provider diagnostics
- retrieval filters

## Hard Constraints

- Do not remove compatibility endpoints before frontend migration.
- Do not drop database tables in the first pass.
- Do not leak provider secrets to the frontend.
- Do not expose lifecycle actions beyond create/start/stop/delete in normal UI.
- Do not scatter raw fetch calls through React components.
- Keep PRs small and phase-based.

## Definition of Done

- Frontend uses `processing-status` only.
- `/operations` is the global async activity API.
- Domain UI exposes only Start, Stop, Delete, with Create elsewhere.
- Provider source of truth is documented and enforced.
- Upload stages are clear and visible.
- Frontend API calls are centralized.
- Tests pass.
```
