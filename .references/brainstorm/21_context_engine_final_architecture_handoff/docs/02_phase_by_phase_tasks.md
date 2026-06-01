# 02 — Phase-by-Phase Tasks

## Phase Summary

```text
Phase 0: Baseline current architecture
Phase 1: Canonicalize document processing-status
Phase 2: Promote operations as async visibility layer
Phase 3: Simplify domain lifecycle to create/start/stop/delete
Phase 4: Clarify provider config source of truth
Phase 5: Clean document upload workflow stages
Phase 6: Centralize frontend API calls
Phase 7: Add database ownership guardrails
Phase 8: Final tests and documentation
```

## Phase 0 Checklist

- [ ] Branch from `v1`.
- [ ] Add `docs/ARCHITECTURE_CURRENT.md`.
- [ ] List all backend routes from `app/main.py` and `app/api/routes`.
- [ ] List all frontend endpoint callers from `client/src`.
- [ ] List all SQLAlchemy models and migrations.
- [ ] Run existing backend tests.
- [ ] Run existing frontend tests/lint.

## Phase 1 Checklist — Status

- [ ] Confirm `processing-status` response shape.
- [ ] Migrate frontend from `ingestion-status` to `processing-status`.
- [ ] Keep deprecated wrappers temporarily.
- [ ] Add tests for both user and admin status endpoints.
- [ ] Add deprecation comments.

## Phase 2 Checklist — Operations

- [ ] Define stable operation response shape.
- [ ] Add/update `OperationService` if needed.
- [ ] Ensure document ingest jobs appear in `/operations`.
- [ ] Ensure domain lifecycle actions appear in `/operations`.
- [ ] Move frontend from `/jobs` to `/operations`.
- [ ] Keep `/jobs` debug-only or deprecated.

## Phase 3 Checklist — Domain Lifecycle

- [ ] Confirm only create/start/stop/delete remain in UI.
- [ ] Remove upload/view/logs from domain More menu.
- [ ] Route domain actions through one domain service.
- [ ] Document desired vs observed state.
- [ ] Ensure each domain lifecycle action creates operation/audit entries.

## Phase 4 Checklist — Provider Config

- [ ] Decide provider source of truth.
- [ ] If env-owned, make provider UI read-only diagnostics.
- [ ] Remove runtime retrieval default editing.
- [ ] Keep embedding fixed per domain.
- [ ] Route provider lookup through one service.

## Phase 5 Checklist — Upload Workflow

- [ ] Express upload stages consistently.
- [ ] Ensure upload response includes document id, operation id, status URL.
- [ ] Ensure worker updates operation stage/progress.
- [ ] Ensure poller updates waiting_remote/ready/failed.
- [ ] Map backend stages to frontend labels.

## Phase 6 Checklist — Frontend API Layer

- [ ] Search for raw `fetch(` calls.
- [ ] Move endpoint strings into `client/src/lib/api`.
- [ ] Add `domains.ts`, `operations.ts`, `provider.ts` if missing.
- [ ] Ensure stores do not duplicate API client logic.
- [ ] Keep components mostly presentational.

## Phase 7 Checklist — Database Guardrails

- [ ] Classify tables as core/optional/deprecated candidate.
- [ ] Do not drop tables in the first cleanup PR.
- [ ] Remove reads before writes.
- [ ] Add migration plan only after code no longer depends on tables.

## Phase 8 Checklist — Finalization

- [ ] Add target architecture docs.
- [ ] Add API contract docs.
- [ ] Add domain lifecycle docs.
- [ ] Add upload workflow docs.
- [ ] Add operations visibility docs.
- [ ] Add provider config docs.
- [ ] Run full backend and frontend tests.
- [ ] Manual QA core flows.
