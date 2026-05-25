---
name: lightrag-cleanup-tdd-grillme
overview: Implement the full LightRAG entropy cleanup end-to-end with strict TDD vertical slices and explicit grill-me decision checkpoints, enforcing fail-hard structure ingestion and removing semantic fallback ambiguity.
todos:
  - id: slice1-config
    content: Implement config hard requirement with red-green-refactor tests.
    status: completed
  - id: slice2-routing
    content: Implement retrieval routing cleanup and remove semantic fallback wiring.
    status: completed
  - id: slice3-local-runtime
    content: Remove local semantic runtime paths while preserving safe migration boundaries.
    status: completed
  - id: slice4-ingestion
    content: Enforce fail-hard ingestion for structure parse failures and required LightRAG upload.
    status: completed
  - id: slice5-status-answer
    content: Harden LightRAG status mapping and remove answer fallback ambiguity.
    status: completed
  - id: slice6-docs-verify
    content: Align docs and run final tests/lints/search-based verification.
    status: completed
isProject: false
---

# Implement Mandatory LightRAG Cleanup (TDD + Grill-Me)

## Scope Confirmed
- Full rollout across config, retrieval routing, ingestion, status handling, answer fallback cleanup, and docs.
- Structure parsing failures will **fail ingestion explicitly** (no raw fallback).

## Execution Style (Required)
- Follow strict RED->GREEN->REFACTOR vertical slices from [`.cursor/skills/engineering/tdd/SKILL.md`](/data/home/tkodippili/Desktop/localTest_context_engine/.cursor/skills/engineering/tdd/SKILL.md).
- At each phase boundary, run a grill-me checkpoint from [`.cursor/skills/grill-me/SKILL.md`](/data/home/tkodippili/Desktop/localTest_context_engine/.cursor/skills/grill-me/SKILL.md): verify assumptions, unresolved branches, and dependency order before proceeding.

## Phase Plan
1. **Config hard requirement (PR-sized slice 1)**
- Files: [`app/core/config.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/core/config.py), [`.env.example`](/data/home/tkodippili/Desktop/localTest_context_engine/.env.example), config tests.
- RED: add failing tests for `LIGHTRAG_ENABLED=false` rejection and missing LightRAG endpoint/domain config.
- GREEN: enforce required LightRAG config and clear startup error messages.
- REFACTOR: normalize config validation and remove ambiguous optional semantics wording.

2. **Retrieval routing cleanup (slice 2)**
- Files: [`app/services/retrieval_service.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/services/retrieval_service.py), [`app/retrieval/routing_policy.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/retrieval/routing_policy.py), [`app/retrieval/router.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/retrieval/router.py), [`app/retrieval/strategies.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/retrieval/strategies.py), query API/schema tests.
- RED: add failing behavior tests proving `semantic`/`hybrid`/`auto` require LightRAG engine and `navigation` remains local only.
- GREEN: remove semantic-to-navigation fallback wiring, enforce mode-to-backend mapping.
- REFACTOR: clarify naming and remove dead/ambiguous parameters.

3. **Remove local semantic runtime usage (slice 3)**
- Files: [`app/services/indexing_service.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/services/indexing_service.py), [`app/storage/repositories/documents.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/storage/repositories/documents.py), [`app/indexing/semantic_index_builder.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/indexing/semantic_index_builder.py), [`app/storage/tables.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/storage/tables.py), related tests.
- RED: tests that fail if runtime calls local semantic chunk build/query paths.
- GREEN: remove runtime references; keep DB table removal as separate safe migration slice if needed.
- REFACTOR: tighten boundaries so tests fake remote LightRAG adapter only.

4. **Ingestion hardening with fail-hard structure policy (slice 4)**
- Files: [`app/services/document_service.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/services/document_service.py), [`app/services/lightrag_ingestion_service.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/services/lightrag_ingestion_service.py), [`app/services/indexing_service.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/services/indexing_service.py), [`app/workers/tasks.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/workers/tasks.py).
- RED: tests asserting uploads require valid LightRAG domain/config and structure parse failure leads to explicit failed ingestion.
- GREEN: remove optional LightRAG ingestion branch and enforce fail-hard ingestion outcomes.
- REFACTOR: standardize error/status payloads for API and job logs.

5. **Status mapping + answer fallback ambiguity cleanup (slice 5)**
- Files: [`app/integrations/lightrag_remote_adapter.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/integrations/lightrag_remote_adapter.py), [`app/schemas/query.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/schemas/query.py), [`app/retrieval/answer_composer.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/retrieval/answer_composer.py), [`app/api/routes/query.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/api/routes/query.py).
- RED: tests for unknown LightRAG statuses (must error/fail explicitly) and evidence-only answer behavior when no grounded evidence exists.
- GREEN: map known statuses only; deprecate/remove `allow_general_fallback` behavior ambiguity.
- REFACTOR: simplify response messaging for “no evidence” states.

6. **Docs alignment + final verification (slice 6)**
- Files: [`README.md`](/data/home/tkodippili/Desktop/localTest_context_engine/README.md), [`docs/architecture.md`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/architecture.md), [`docs/junior_dev_start_here.md`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/junior_dev_start_here.md), [`docs/implementation-plan.md`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/implementation-plan.md), [`docs/implementation-status.md`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/implementation-status.md).
- RED: doc consistency check list (semantic fallback language must be gone).
- GREEN: update all canonical docs to the enforced architecture and mode semantics.
- REFACTOR: remove stale references and duplication.

## Dependency Order
- Config enforcement precedes retrieval/ingestion changes.
- Retrieval boundary cleanup precedes runtime local semantic code removal.
- Ingestion/status hardening precedes answer/documentation finalization.

## Grill-Me Checkpoints
- After each slice: verify no hidden fallback was introduced, naming remains explicit, and tests assert behavior through public interfaces.
- Before final merge: challenge all remaining branches (`auto`, status unknowns, parser failures, adapter outages) and ensure explicit outcomes.

## Verification Strategy
- Run targeted tests after each slice, then full suite near the end.
- Run lint diagnostics on touched files and fix introduced issues.
- Run repo-wide searches for forbidden fallback patterns (`semantic_engine=self.navigation_engine`, local semantic chunk runtime calls, ambiguous fallback flags).