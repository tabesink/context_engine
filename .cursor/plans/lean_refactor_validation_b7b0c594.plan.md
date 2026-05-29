---
name: Lean Refactor Validation
overview: Validate the brainstorm package against the current checkout, then implement only the live gaps and behavior-preserving frontend polish using TDD-style vertical slices.
todos:
  - id: impact-before-edits
    content: Run/confirm GitNexus impact for backend and frontend symbols before editing.
    status: completed
  - id: backend-url-helper
    content: Add asset URL helper tests, implement helper, and replace duplicated backend URL strings.
    status: completed
  - id: frontend-source-polish
    content: Add focused frontend test coverage and render secondary source-context figures without reshuffling the panel.
    status: in_progress
  - id: validation
    content: Run focused backend/frontend validation and check lints on edited files.
    status: pending
isProject: false
---

# Lean Refactor Validation And Implementation

## Validation Result

The package is partially stale against this checkout. Several planned items are already implemented:

- Backend workspace context route already exists in [`/data/home/tkodippili/Desktop/localTest_context_engine/app/api/routes/workspace_tree.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/api/routes/workspace_tree.py), and is covered in [`/data/home/tkodippili/Desktop/localTest_context_engine/tests/test_api.py`](/data/home/tkodippili/Desktop/localTest_context_engine/tests/test_api.py).
- `workspace_node_id` already exists in [`/data/home/tkodippili/Desktop/localTest_context_engine/app/schemas/retrieval.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/schemas/retrieval.py) and is mapped in [`/data/home/tkodippili/Desktop/localTest_context_engine/app/retrieval/evidence_mapper.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/retrieval/evidence_mapper.py).
- Frontend source context client, source navigator state, two-tab panel behavior, tree selection, and asset cards already exist in [`/data/home/tkodippili/Desktop/localTest_context_engine/client/src/api/workspace-context.ts`](/data/home/tkodippili/Desktop/localTest_context_engine/client/src/api/workspace-context.ts), [`/data/home/tkodippili/Desktop/localTest_context_engine/client/src/components/chat/LightRagChatShell.tsx`](/data/home/tkodippili/Desktop/localTest_context_engine/client/src/components/chat/LightRagChatShell.tsx), [`/data/home/tkodippili/Desktop/localTest_context_engine/client/src/components/chat/SidePanel.tsx`](/data/home/tkodippili/Desktop/localTest_context_engine/client/src/components/chat/SidePanel.tsx), and [`/data/home/tkodippili/Desktop/localTest_context_engine/client/src/components/chat/AssetCards.tsx`](/data/home/tkodippili/Desktop/localTest_context_engine/client/src/components/chat/AssetCards.tsx).

The remaining validated gaps are:

- Asset URL construction is still duplicated in [`/data/home/tkodippili/Desktop/localTest_context_engine/app/services/workspace_tree_service.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/services/workspace_tree_service.py), [`/data/home/tkodippili/Desktop/localTest_context_engine/app/services/workspace_context_service.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/services/workspace_context_service.py), and [`/data/home/tkodippili/Desktop/localTest_context_engine/app/services/retrieval_asset_resolver.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/services/retrieval_asset_resolver.py).
- Source Navigator currently computes `secondaryFigures` but does not render them, so source contexts with multiple figures can silently drop all but the primary figure.
- Frontend source-navigation behavior has limited direct test coverage; add focused tests before any behavior-preserving cleanup.

## Design Gates Chosen

- Keep `workspace-context` in `workspace_tree.py` for now. Pros: smallest diff, route is live and tested, avoids churn. Cons: route module ownership is less pure. Recommendation accepted: keep it until the module grows.
- Frontend polish should be behavior-preserving with focused tests. Pros: reduces regression risk and avoids a broad UI reshuffle. Cons: `SidePanel.tsx` remains large. Recommendation accepted: do not split components now.
- Asset URL helper should URL-encode path components. Pros: safer for non-simple IDs and one canonical contract. Cons: tests must confirm existing UUID/simple IDs remain unchanged. Recommendation: add helper tests for both simple IDs and IDs requiring escaping.

## Implementation Plan

1. Run GitNexus impact before each symbol edit and report any HIGH/CRITICAL result before proceeding. Current pre-check for the backend URL symbols is LOW and limited to the workspace-tree flow.
2. TDD slice 1: add tests for a new backend asset URL helper, including simple IDs and escaped IDs.
3. Implement [`/data/home/tkodippili/Desktop/localTest_context_engine/app/services/asset_urls.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/services/asset_urls.py), then replace duplicated URL construction in the three backend services.
4. TDD slice 2: add or update frontend utility/component-level tests for source-context asset handling, especially multiple figures from a workspace source context.
5. Implement the smallest frontend polish needed to render secondary source-context figures while preserving current panel behavior and styles.
6. Run focused validation first, then broader validation if the focused checks pass:
   - `python -m pytest tests/test_workspace_context_service.py tests/test_evidence_mapper.py tests/test_api.py -q` or narrower equivalent if runtime is high.
   - Client tests/build/lint for touched frontend files, using the project’s existing scripts.
7. After edits, run `gitnexus_detect_changes()` before any commit request and use `ReadLints` on edited files.

## TDD Guardrails

- One test, one implementation step, then repeat.
- Tests should verify public behavior: API response URLs, source-context asset rendering behavior, and retrieval/source navigation contracts.
- No CLI code or docs under `docs/brainstorm/` will be modified.
- No broad component split unless a test exposes a concrete need.