---
name: Deviation Rectification
overview: Rectify the documentation/code deviations found in the review, then implement the architecture deepening candidates in small steps with matching tests and documentation updates after each slice.
todos:
  - id: fix-cli-deviations
    content: Fix CLI flag/doc mismatches for query debug and LightRAG graph depth/node options, with tests and docs.
    status: completed
  - id: fix-lightrag-domain
    content: Align LightRAG retrieval domain behavior between code, tests, and HTTP contract docs.
    status: completed
  - id: fix-document-policy
    content: Align ready-document read policy between document routes, tests, and architecture docs.
    status: completed
  - id: fix-weak-evidence
    content: Implement or clarify weak-evidence refusal behavior and update answer tests/docs.
    status: completed
  - id: clarify-indexing-adr
    content: Update ADR/indexing docs to match current in-place indexing behavior and hardening target.
    status: completed
  - id: deepen-routing-policy
    content: Extract and test the retrieval routing policy Module for local versus remote mode decisions.
    status: completed
  - id: deepen-remote-seam
    content: Refine the remote retrieval seam so local and remote retrieval strategies are easier to substitute and test.
    status: completed
  - id: deepen-evidence-mapping
    content: Remove evidence DTO round-tripping or centralize mapping so answer composition uses domain evidence safely.
    status: completed
  - id: reduce-cli-schema-coupling
    content: Concentrate CLI query payload construction to reduce schema drift while preserving API-client behavior.
    status: completed
  - id: validate-alignment
    content: Run targeted tests, lint checks, and canonical-doc consistency searches after implementation.
    status: completed
isProject: false
---

# Deviation Rectification And Architecture Deepening Plan

## Scope

Address the concrete deviations found in the documentation review and then implement the four deepening candidates from the architecture review:

- Retrieval routing policy Module
- Remote retrieval Seam
- Evidence mapping depth
- CLI/schema coupling

Keep documentation synchronized as each code slice lands. Continue excluding [`docs/brainstorm/`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/brainstorm/) and [`.pytest_cache`](/data/home/tkodippili/Desktop/localTest_context_engine/.pytest_cache) from edits.

## Phase 1: Fix Concrete Deviations

1. Correct CLI command/documentation mismatches.
   - Inspect [`cli/main.py`](/data/home/tkodippili/Desktop/localTest_context_engine/cli/main.py), [`tests/test_cli.py`](/data/home/tkodippili/Desktop/localTest_context_engine/tests/test_cli.py), and [`docs/cli_docs/commands.md`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/cli_docs/commands.md).
   - Choose code-first fixes where the documented behavior is useful:
     - Add `--include-debug` as a CLI alias for the existing query debug flag while preserving `--debug` if possible.
     - Add `--max-depth` and `--max-nodes` to `ragcli lightrag graphs show`, forwarding them to `GET /graphs`.
   - Update CLI docs and API contract examples to match the final command surface.
   - Add/adjust CLI tests for the new flags.

2. Resolve LightRAG retrieval `domain` behavior.
   - Inspect [`app/retrieval/lightrag_remote_engine.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/retrieval/lightrag_remote_engine.py), [`app/integrations/lightrag_remote_adapter.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/integrations/lightrag_remote_adapter.py), and [`app/integrations/lightrag_domains.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/integrations/lightrag_domains.py).
   - Prefer code alignment: pass the configured `LIGHTRAG_DOMAIN` into remote retrieval so the current [`docs/lightrag_docs/http-contract.md`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/lightrag_docs/http-contract.md) sample is true.
   - Update adapter tests to assert `domain` is sent when configured and omitted only when intentionally absent.

3. Resolve ready-document policy drift.
   - Inspect [`app/api/routes/documents.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/api/routes/documents.py), [`app/services/document_service.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/services/document_service.py), and document route tests.
   - Decide in code that user-facing document reads should match the docs: ready and non-deleted only.
   - Wire existing `DocumentService.get_ready_or_404` or equivalent into document detail/structure/page paths where appropriate.
   - Add tests for non-ready document visibility.
   - Update docs only if a route intentionally remains broader for admin/operator use.

4. Clarify weak-evidence behavior.
   - Inspect [`app/retrieval/answer_composer.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/retrieval/answer_composer.py), query schemas, and answer tests.
   - Implement a minimal, explicit weak-evidence rule if the current docs should remain true, for example a small score threshold applied only when all available evidence is low-confidence.
   - Keep empty-evidence behavior intact.
   - Add tests for empty evidence, weak evidence with fallback disabled, and weak evidence with `allow_general_fallback=true`.
   - Update [`docs/architecture.md`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/architecture.md) and [`docs/implementation-plan.md`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/implementation-plan.md) with the exact rule.

5. Reconcile indexing ADR wording with implementation.
   - Inspect [`app/services/indexing_service.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/services/indexing_service.py) and indexing tests.
   - Avoid a large transactional/index-version rewrite in this pass unless tests show user-facing breakage.
   - Update [`docs/adr/0003-indexing-job-model.md`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/adr/0003-indexing-job-model.md) to accurately state current single-row/in-place indexing behavior and the hardening target.

## Phase 2: Deepen Retrieval Routing Policy

Create a focused routing policy Module that owns the `LIGHTRAG_ENABLED` by `RetrievalMode` matrix.

- Candidate files:
  - [`app/services/retrieval_service.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/services/retrieval_service.py)
  - [`app/retrieval/router.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/retrieval/router.py)
  - New small Module under [`app/retrieval/`](/data/home/tkodippili/Desktop/localTest_context_engine/app/retrieval/), if needed
- Move mode/flag decisions out of `RetrievalService` into table-driven policy code.
- Add focused tests for the policy matrix:
  - LightRAG disabled: all modes local
  - LightRAG enabled: `auto`, `semantic`, `hybrid` remote
  - LightRAG enabled: `navigation` local
- Update docs to point to the policy instead of restating behavior inconsistently.

## Phase 3: Deepen The Remote Retrieval Seam

Make local and remote retrieval substitution clearer without changing the public HTTP contract.

- Candidate files:
  - [`app/retrieval/base.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/retrieval/base.py)
  - [`app/retrieval/lightrag_remote_engine.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/retrieval/lightrag_remote_engine.py)
  - [`app/services/retrieval_service.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/services/retrieval_service.py)
- Introduce or refine a cohesive retrieval strategy interface that can represent local routing and remote LightRAG routing behind one seam.
- Preserve the existing `Evidence` contract.
- Reduce monkeypatch-heavy tests by allowing retrieval strategies/adapters to be injected or constructed through a narrow factory.
- Update ADR/docs language only if the seam changes the implementation model in a meaningful way.

## Phase 4: Deepen Evidence Mapping

Remove DTO round-tripping in the answer path and concentrate Evidence serialization logic.

- Candidate files:
  - [`app/services/retrieval_service.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/services/retrieval_service.py)
  - [`app/schemas/query.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/schemas/query.py)
  - [`app/domain/models.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/domain/models.py)
  - [`app/retrieval/answer_composer.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/retrieval/answer_composer.py)
- Make `AnswerComposer` consume domain `Evidence` from `RetrievalResult` directly, or introduce one mapper Module for domain-to-response conversion.
- Preserve API response field names such as `evidence_id`.
- Add tests that section/page metadata survives retrieval-to-answer composition.
- Update [`docs/architecture.md`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/architecture.md) to distinguish internal `Evidence.id` from public `evidence_id`.

## Phase 5: Reduce CLI/Schema Coupling

Concentrate query payload construction so CLI/API drift is less likely.

- Candidate files:
  - [`cli/main.py`](/data/home/tkodippili/Desktop/localTest_context_engine/cli/main.py)
  - [`app/schemas/query.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/schemas/query.py)
  - [`tests/test_cli.py`](/data/home/tkodippili/Desktop/localTest_context_engine/tests/test_cli.py)
- Keep the CLI as an HTTP client, but make payload construction less stringly-typed.
- Prefer a small shared payload helper or schema-backed construction that still avoids importing backend business logic into CLI command handlers.
- Add CLI tests that catch schema field drift for query commands.
- Update [`docs/cli_docs/api-contract.md`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/cli_docs/api-contract.md) if any payload examples change.

## Phase 6: Validation

After each phase:

- Run targeted tests for touched code.
- Run `ReadLints` on edited files.
- Search canonical docs for stale strings such as `/query/context`, `/lightrag/graph`, `deploy-lightrag.sh`, unsupported CLI flags, and unconditional pgvector claims.
- Keep `docs/brainstorm/**`, `.pytest_cache`, and the existing plan file untouched unless explicitly requested.

Final validation should include:

- CLI tests
- API tests around documents/query/LightRAG
- LightRAG adapter tests
- Any focused new unit tests for routing policy, evidence mapping, and answer composer behavior