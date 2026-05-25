---
name: Evidence Panel Docs
overview: Reconcile the evidence-panel documentation with the backend that already ships `POST /retrieve` and intentionally removes `/query/*`. Create a docs-only `IMPLEMENT.md` that makes the remaining backend evidence-reporting decisions explicit and frames future code work as vertical TDD slices.
todos:
  - id: draft-implement
    content: Create `IMPLEMENT.md` with backend baseline, tensions, resolved decisions, and TDD implementation sequence.
    status: completed
  - id: reconcile-overview-docs
    content: Update package index, README, executive summary, architecture decision, and backend plan for retrieve-only backend reality.
    status: completed
  - id: reconcile-contract-tests
    content: Update API contract, rollout, and test plan to remove `/query/retrieve` alias expectations and highlight remaining test gaps.
    status: completed
  - id: reconcile-agent-materials
    content: Update checklist and prompts so future work inspects current files and follows vertical TDD slices.
    status: completed
  - id: verify-doc-consistency
    content: Search the evidence-panel package for stale compatibility language and summarize any intentional historical references.
    status: completed
isProject: false
---

# Evidence Panel Documentation Plan

## Confirmed Direction

- Treat `POST /retrieve` as the only supported evidence retrieval endpoint for the right-hand evidence panel.
- Keep `/query/retrieve` removed; update stale migration/compatibility language instead of planning to restore an alias.
- Make this pass documentation-only: no backend code, no tests, no route changes.

## Backend Facts To Anchor The Docs

- [`/data/home/tkodippili/Desktop/localTest_context_engine/app/api/routes/retrieve.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/api/routes/retrieve.py) already exposes `POST /retrieve` as a thin wrapper around `RetrievalService(session).retrieve(...)`.
- [`/data/home/tkodippili/Desktop/localTest_context_engine/app/schemas/retrieval.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/schemas/retrieval.py) has the current `RetrieveRequest`, `EvidenceResponse`, `AssetResponse`, and `RetrieveResponse` contract.
- [`/data/home/tkodippili/Desktop/localTest_context_engine/app/retrieval/evidence_mapper.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/retrieval/evidence_mapper.py) currently maps core evidence fields, but does not promote `source_path`, `document_title`, `chunk_id`, or `reference_id` to top-level response fields.
- [`/data/home/tkodippili/Desktop/localTest_context_engine/tests/test_api.py`](/data/home/tkodippili/Desktop/localTest_context_engine/tests/test_api.py) currently asserts `/query/retrieve` returns 404, so docs must not claim it remains compatible.

## Tensions And Design Decisions To Document

- API direction: retrieve-only is now the canonical backend surface; `/query/retrieve` compatibility guidance is stale.
- Evidence display contract: the panel can render basic cards today from `metadata`, but future backend work should decide whether to promote display helpers to explicit top-level fields.
- Document labels: `document_title` is not currently populated by retrieval; future implementation must decide whether it comes from metadata, `DocumentRepository`, or remains a WebUI fallback.
- Asset linkage: assets are top-level response items, not nested under evidence; docs should clarify how the WebUI correlates evidence metadata and `assets[]`.
- Debug visibility: future tests should preserve admin-only debug behavior through the public `/retrieve` interface.
- Scope boundary: evidence panel docs should stay separate from the workspace tree docs; the tree scopes/browses, while `/retrieve` reports per-query evidence.

## Documentation Edits

- Create [`/data/home/tkodippili/Desktop/localTest_context_engine/docs/brainstorm/12_context_engine_evidence_panel/IMPLEMENT.md`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/brainstorm/12_context_engine_evidence_panel/IMPLEMENT.md) as the consolidated implementation guide.
- Update [`IMPLEMENTATION_PACKAGE_INDEX.md`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/brainstorm/12_context_engine_evidence_panel/IMPLEMENTATION_PACKAGE_INDEX.md) and [`README.md`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/brainstorm/12_context_engine_evidence_panel/README.md) so the package points first to `IMPLEMENT.md` and no longer lists `/query/retrieve` as required.
- Update [`docs/00_EXECUTIVE_SUMMARY.md`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/brainstorm/12_context_engine_evidence_panel/docs/00_EXECUTIVE_SUMMARY.md), [`docs/01_ARCHITECTURE_DECISION.md`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/brainstorm/12_context_engine_evidence_panel/docs/01_ARCHITECTURE_DECISION.md), and [`docs/02_BACKEND_IMPLEMENTATION_PLAN.md`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/brainstorm/12_context_engine_evidence_panel/docs/02_BACKEND_IMPLEMENTATION_PLAN.md) to reflect implemented baseline plus remaining decisions.
- Update [`contracts/retrieve_api_contract.md`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/brainstorm/12_context_engine_evidence_panel/contracts/retrieve_api_contract.md), [`docs/04_TEST_PLAN.md`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/brainstorm/12_context_engine_evidence_panel/docs/04_TEST_PLAN.md), and [`docs/05_ROLLOUT_AND_BACKWARD_COMPATIBILITY.md`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/brainstorm/12_context_engine_evidence_panel/docs/05_ROLLOUT_AND_BACKWARD_COMPATIBILITY.md) to remove alias requirements and preserve retrieve-only rollout/test expectations.
- Update [`checklists/junior_dev_checklist.md`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/brainstorm/12_context_engine_evidence_panel/checklists/junior_dev_checklist.md), [`prompts/coding_agent_prompt.md`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/brainstorm/12_context_engine_evidence_panel/prompts/coding_agent_prompt.md), and [`prompts/review_prompt.md`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/brainstorm/12_context_engine_evidence_panel/prompts/review_prompt.md) so future agents inspect the actual retrieve route and use TDD vertical slices.

## TDD Shape For Future Backend Work

- First tracer bullet: one public API or mapper test for one display-field behavior, then minimal schema/mapper change.
- Next slice: one public `/retrieve` behavior test for admin-only debug or empty evidence, then minimal implementation only if needed.
- Later slice: asset/evidence correlation contract tests if WebUI needs stronger linkage than metadata plus top-level `assets[]`.
- Refactor only after each slice is green; avoid bulk speculative tests for imagined fields.

## Validation

- Since the work is docs-only, verify by searching the package for stale `/query/retrieve`, `query.py`, and alias language.
- Do not run backend tests unless a later approved scope includes code changes.