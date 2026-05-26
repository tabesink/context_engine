---
name: lean_lightrag_502_contract
overview: Apply the smallest backend-only contract fix so failed lifecycle operations return HTTP 502, while preserving existing service behavior and frontend code.
todos:
  - id: impact-analysis
    content: Run GitNexus upstream impact analysis for `_operation_or_404` and confirm risk before edits
    status: completed
  - id: backend-helper-contract
    content: Modify `_operation_or_404` to map failed operation result status to HTTP 502 with structured detail
    status: completed
  - id: contract-tests
    content: Add minimal tests for failed->502 and succeeded->pass-through behavior in `tests/test_api.py` and run targeted test subset
    status: completed
isProject: false
---

# Lean Backend Contract Fix for Domain Lifecycle

## Goal
Align lifecycle command semantics so HTTP status reflects operation outcome, using a single existing choke point and no frontend/service bloat.

## Scope (intentionally narrow)
- Change only helper logic in [`/data/home/tkodippili/Desktop/localTest_context_engine/app/api/routes/lightrag_admin.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/api/routes/lightrag_admin.py).
- Add only targeted tests in existing test modules.
- Do not add new helper layers, wrapper types, service exceptions, or frontend guards.

## Planned Changes
- Update `_operation_or_404()` in [`/data/home/tkodippili/Desktop/localTest_context_engine/app/api/routes/lightrag_admin.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/api/routes/lightrag_admin.py):
  - Keep current `DomainNotFoundError -> 404` mapping.
  - If returned `LightRAGDomainOperationResult.status != "succeeded"`, raise `HTTPException(status_code=502, detail={...})` with fields:
    - `code: "lightrag_domain_operation_failed"`
    - `domain_id`, `operation`, `status`, `service_name`, `message`
  - Return result unchanged when status is `succeeded`.
- Leave route bodies unchanged (`up/down/recreate` already flow through `_operation_or_404()`).
- Leave `LightRAGDomainService` unchanged (still returns operation result and persists manifest/runtime status).

## Test Plan (TDD)
1. Preserve service behavior (already covered):
   - Reuse/confirm existing failure test in [`/data/home/tkodippili/Desktop/localTest_context_engine/tests/test_lightrag_deploy_service.py`](/data/home/tkodippili/Desktop/localTest_context_engine/tests/test_lightrag_deploy_service.py) that asserts failed docker command yields `result.status == "failed"`.
2. Add helper/route-contract tests in [`/data/home/tkodippili/Desktop/localTest_context_engine/tests/test_api.py`](/data/home/tkodippili/Desktop/localTest_context_engine/tests/test_api.py):
   - Failed operation result maps to `HTTP 502` with structured `detail` payload.
   - Successful operation result returns normally.
3. Keep existing admin lifecycle endpoint tests green (same file), ensuring no regression for successful paths.

## Safety and Validation
- Before editing `_operation_or_404`, run GitNexus impact analysis for symbol blast radius (`gitnexus_impact` upstream) and report risk.
- Execute targeted tests:
  - `tests/test_lightrag_deploy_service.py`
  - focused `tests/test_api.py` cases for lifecycle operation mapping
- Confirm no frontend changes required because existing API client already throws on non-2xx responses.

## Expected Outcome
- `200`: lifecycle command succeeded.
- `404`: domain not found.
- `400`: deploy disabled or bad request.
- `502`: Docker/LightRAG runtime command failed.
- UI naturally shows error through existing request error path, with no additional frontend logic.