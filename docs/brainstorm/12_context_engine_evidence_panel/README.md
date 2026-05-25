# Context Engine Evidence Side Panel Implementation Package

This package guides a junior developer or coding agent to extend `context_engine` so the WebUI can display retrieved evidence in a right-hand side panel.

The intended implementation is lean:

- Reuse the existing retrieval pipeline.
- Reuse the existing `RetrieveResponse.evidence` and `assets` response shape.
- Do not import or duplicate the `easy-deploy-lightrag` backend wrapper.
- Use the clean `POST /retrieve` endpoint for evidence-only retrieval.
- Keep answer generation separate from evidence retrieval.
- Keep removed `/query/*` routes removed unless a future product decision explicitly reintroduces one.

## Package Contents

| File | Purpose |
|---|---|
| `IMPLEMENT.md` | Consolidated implementation guide, current backend baseline, design tensions, and future TDD slices. |
| `docs/00_EXECUTIVE_SUMMARY.md` | High-level goal, current repo facts, and implementation strategy. |
| `docs/01_ARCHITECTURE_DECISION.md` | Backend/WebUI boundary and why this should be evidence-only. |
| `docs/02_BACKEND_IMPLEMENTATION_PLAN.md` | Step-by-step backend implementation plan. |
| `docs/03_WEBUI_IMPLEMENTATION_CONTRACT.md` | WebUI right-side panel data contract and UI behavior. |
| `docs/04_TEST_PLAN.md` | Unit, integration, and API tests to add/update. |
| `docs/05_ROLLOUT_AND_BACKWARD_COMPATIBILITY.md` | Retrieve-only rollout notes and compatibility boundaries. |
| `contracts/retrieve_api_contract.md` | Request/response contract with examples. |
| `contracts/evidence_item_contract.md` | Normalized evidence-card field contract. |
| `checklists/junior_dev_checklist.md` | Concrete implementation checklist. |
| `prompts/coding_agent_prompt.md` | Copy-paste prompt for a coding agent. |
| `prompts/review_prompt.md` | Copy-paste prompt for post-implementation review. |

## Recommended Order

1. Read `IMPLEMENT.md`.
2. Read `docs/00_EXECUTIVE_SUMMARY.md`.
3. Read `docs/01_ARCHITECTURE_DECISION.md`.
4. Implement any approved backend changes from `docs/02_BACKEND_IMPLEMENTATION_PLAN.md`.
5. Wire the WebUI using `docs/03_WEBUI_IMPLEMENTATION_CONTRACT.md`.
6. Run the tests from `docs/04_TEST_PLAN.md`.
7. Use `checklists/junior_dev_checklist.md` before opening the PR.

## Non-Goals

Do not add a new chat engine.
Do not add duplicate auth.
Do not add duplicate `/api/v1/auth/*` routes.
Do not persist evidence unless the product explicitly needs retrieval history.
Do not call LightRAG directly from the WebUI.
Do not bypass `context_engine` auth and domain validation.
