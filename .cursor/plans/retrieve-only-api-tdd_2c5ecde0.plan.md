---
name: retrieve-only-api-tdd
overview: Refactor the backend and CLI from `/query*` endpoints to a single retrieve-only contract (`POST /retrieve`) using a TDD red-green-refactor sequence, while removing answer-generation surface and updating tests/docs.
todos:
  - id: tdd-slice-1-api-route
    content: Write failing API contract tests for `/retrieve` success and `/query*` removal, then implement new route wiring and remove old route module.
    status: completed
  - id: tdd-slice-2-schemas
    content: Migrate query schema names/usages to retrieval schema names and remove `QueryResponse`/fallback artifacts.
    status: completed
  - id: tdd-slice-3-service
    content: Delete RetrievalService answer path and AnswerComposer integration while preserving retrieve behavior.
    status: completed
  - id: tdd-slice-4-cli-tui
    content: Migrate CLI/TUI request paths and payload builders to `/retrieve`, and remove answer-oriented flows/screens.
    status: completed
  - id: tdd-slice-5-tests-docs
    content: Update/remove impacted tests and docs, then run full validation sweep and regression checks.
    status: completed
isProject: false
---

# Retrieve-Only API Refactor Plan

## Scope and Constraints
- Implement the retrieve-only target in [docs/brainstorm/08_context_only_retrieval_plan/context_engine_retrieve_only.md](/data/home/tkodippili/Desktop/localTest_context_engine/docs/brainstorm/08_context_only_retrieval_plan/context_engine_retrieve_only.md).
- Apply TDD as vertical slices (one failing behavior test at a time, then minimal implementation).
- Treat `.cursor/skills/tdd` as the intended TDD skill reference (since `.cursor/skills/engineering/tdd` is not present).
- Keep retrieval engines/routing behavior unchanged (Navigation + LightRAG backend behavior remains as-is).
- Do not do optional DB/table naming cleanup in this pass.

## Implementation Slices (TDD)

### Slice 1: New public route contract (`POST /retrieve`)
- RED: add API tests in [tests/test_api.py](/data/home/tkodippili/Desktop/localTest_context_engine/tests/test_api.py) asserting:
  - `POST /retrieve` returns retrieval payload with `evidence` and no `answer`.
  - `POST /query`, `POST /query/answer`, `POST /query/retrieve` return `404` (final-state tests).
- GREEN: create [app/api/routes/retrieve.py](/data/home/tkodippili/Desktop/localTest_context_engine/app/api/routes/retrieve.py), wire it in [app/main.py](/data/home/tkodippili/Desktop/localTest_context_engine/app/main.py), remove old query router file [app/api/routes/query.py](/data/home/tkodippili/Desktop/localTest_context_engine/app/api/routes/query.py).

### Slice 2: Schema rename/query-surface removal
- RED: update/add schema-facing tests to expect retrieve naming and no answer schema usage.
- GREEN:
  - Replace [app/schemas/query.py](/data/home/tkodippili/Desktop/localTest_context_engine/app/schemas/query.py) with retrieval naming (`RetrieveRequest`, `RetrieveResponse`, `EvidenceResponse`, `AssetResponse`).
  - Remove `QueryResponse` and any `allow_general_fallback` usage.
  - Update imports in backend and tests that currently use query schema names.

### Slice 3: Retrieval service answer-path deletion
- RED: service/API tests fail if answer-path APIs are still reachable or if retrieval response includes answer fields.
- GREEN in [app/services/retrieval_service.py](/data/home/tkodippili/Desktop/localTest_context_engine/app/services/retrieval_service.py):
  - Remove `answer()` and `AnswerComposer` dependency.
  - Keep `retrieve()` and existing retrieval execution pipeline.
  - Update type hints/imports to retrieval schema names only.
- Remove [app/retrieval/answer_composer.py](/data/home/tkodippili/Desktop/localTest_context_engine/app/retrieval/answer_composer.py) and its tests when no references remain.

### Slice 4: CLI/TUI migrate to `/retrieve` only
- RED: CLI tests fail for old `/query/*` calls and answer-screen flows.
- GREEN:
  - Update [cli/services/retrieval.py](/data/home/tkodippili/Desktop/localTest_context_engine/cli/services/retrieval.py) to call only `POST /retrieve`.
  - Rename payload builder [cli/query_payload.py](/data/home/tkodippili/Desktop/localTest_context_engine/cli/query_payload.py) to retrieve naming and preserve `lightrag_domain_id` support.
  - Update compare flow [cli/flows/retrieval_compare.py](/data/home/tkodippili/Desktop/localTest_context_engine/cli/flows/retrieval_compare.py) to use `/retrieve`.
  - Remove answer-related TUI actions/screens from [cli/tui/screens/content.py](/data/home/tkodippili/Desktop/localTest_context_engine/cli/tui/screens/content.py) and [cli/screens/retrieval.py](/data/home/tkodippili/Desktop/localTest_context_engine/cli/screens/retrieval.py).

### Slice 5: Test suite + docs cleanup
- Update impacted tests:
  - [tests/test_api.py](/data/home/tkodippili/Desktop/localTest_context_engine/tests/test_api.py)
  - [tests/test_cli_services.py](/data/home/tkodippili/Desktop/localTest_context_engine/tests/test_cli_services.py)
  - [tests/test_cli_query_payload.py](/data/home/tkodippili/Desktop/localTest_context_engine/tests/test_cli_query_payload.py) (or renamed equivalent)
  - [tests/test_cli_tui.py](/data/home/tkodippili/Desktop/localTest_context_engine/tests/test_cli_tui.py)
  - [tests/test_cli_screen_renderers.py](/data/home/tkodippili/Desktop/localTest_context_engine/tests/test_cli_screen_renderers.py)
  - [tests/test_answer_composer.py](/data/home/tkodippili/Desktop/localTest_context_engine/tests/test_answer_composer.py) (delete if unused)
- Update docs/prompts/examples that reference `/query*` endpoints.

## Validation Gates
- Run targeted tests per slice, then full suite (`python -m pytest -q`).
- Run a final reference sweep: `/query`, `QueryResponse`, `AnswerComposer`, `allow_general_fallback` in app/cli/tests/docs.
- Confirm no regressions to LightRAG upstream adapter route (`/query/data`) and admin query-log endpoints (out of scope for renaming in this pass).