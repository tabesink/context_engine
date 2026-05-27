# Context Engine Two-Tab Right Panel Implementation Package

This package contains implementation guidance for adding a two-tab right-hand panel to the Context Engine chat interface.

## Goal

The existing right-hand side panel should support two related but distinct workflows:

1. **Context Stream** — retrieved context/evidence generated during chat retrieval for the selected assistant response.
2. **Source Navigator** — deterministic source inspection when the user clicks a document, section, page, chunk, or asset in the workspace tree.

The central rule is:

> Retrieval populates the Context Stream tab. Workspace-tree clicks populate the Source Navigator tab. A tree click must not silently run retrieval or alter retrieval scope.

## Documents

- `01_architecture_decisions.md` — product, UX, state, and separation-of-concerns decisions.
- `02_backend_implementation_plan.md` — FastAPI schemas, service, route, security, and test plan.
- `03_frontend_implementation_plan.md` — React/Next client state, components, tabs, tree click behavior, and API wiring.
- `04_api_contracts.md` — proposed request/response contracts and TypeScript types.
- `05_testing_and_acceptance.md` — backend/frontend test matrix and acceptance criteria.
- `06_coding_agent_prompt.md` — copy/paste prompt for a coding agent.
- `07_junior_dev_checklist.md` — step-by-step implementation checklist for a junior developer.
- `08_patch_targets.md` — exact likely files to modify or add.

## Recommended implementation order

1. Add backend source-context schema and endpoint.
2. Add backend service that resolves a workspace-tree node into exact source context.
3. Add tests for document/section/page/chunk/asset source inspection.
4. Update frontend API/types to fetch source context.
5. Refactor `SidePanel.tsx` into two tabs.
6. Wire `WorkspaceTree.tsx` node clicks to open the Source Navigator tab.
7. Add evidence-item `Open source` affordance.
8. Run backend tests, frontend lint/build, and manual UX checks.
