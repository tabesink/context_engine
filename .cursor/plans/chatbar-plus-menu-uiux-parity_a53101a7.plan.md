---
name: chatbar-plus-menu-uiux-parity
overview: Implement ChatGPT-inspired left-side plus-menu parity in chat composer while keeping DESIGN.md constraints, with admin-only Upload entry and Retrieval entry that only selects healthy deployed knowledge graphs. Move advanced retrieval tunables out of chat popover and manage them as domain-level defaults in the domain creation flow.
todos:
  - id: ux-plus-menu
    content: Design and implement plus-trigger popup menu in chat composer with DESIGN.md parity and admin-gated Upload item
    status: completed
  - id: retrieval-selector-scope
    content: Reduce retrieval popup to healthy-domain selection only and remove user-facing numeric tuning controls
    status: completed
  - id: domain-defaults-model
    content: Add domain-level retrieval defaults to create-domain frontend/backend models, persistence, and list API response
    status: completed
  - id: chat-default-binding
    content: Bind selected domain retrieval defaults into chat shell request settings
    status: completed
  - id: verify-tests
    content: Add/update tests and run lint/targeted suites for changed frontend and backend modules
    status: completed
isProject: false
---

# Chatbar Plus Menu + Retrieval Routing Plan

## Outcome
- Replace the current single left icon in chat composer with a ChatGPT-style `+` trigger and compact popup menu inspired by the provided references.
- Menu entries:
  - `Upload` (visible to admins only).
  - `Retrieval` (all users), which opens inline retrieval controls.
- Retrieval controls are reduced to deployed KG selection only (healthy domains only).
- Advanced retrieval tunables (`top_k`, `chunk_top_k`, `chunk_rerank_top_k`, `max_token_for_text_unit`, `max_token_for_global_context`, `max_token_for_local_context`) become domain defaults configured in domain creation/admin flow.

## Files and Changes
- Chat composer/menu UX
  - [`/data/home/tkodippili/Desktop/localTest_context_engine/client/src/components/chat/ChatComposer.tsx`](/data/home/tkodippili/Desktop/localTest_context_engine/client/src/components/chat/ChatComposer.tsx)
  - Add left `+` trigger and popup menu pattern (flat panel, no shadow, 12px container radius, pill interactive controls).
  - Gate `Upload` entry by `selectIsAdmin` from [`/data/home/tkodippili/Desktop/localTest_context_engine/client/src/stores/auth-store.ts`](/data/home/tkodippili/Desktop/localTest_context_engine/client/src/stores/auth-store.ts).

- Retrieval inline route behavior
  - [`/data/home/tkodippili/Desktop/localTest_context_engine/client/src/components/chat/RetrievalSettingsPopover.tsx`](/data/home/tkodippili/Desktop/localTest_context_engine/client/src/components/chat/RetrievalSettingsPopover.tsx)
  - Convert to KG-selector-only UI for end users (remove numeric tuning controls from this popup).
  - Filter selectable domains to healthy deployed entries only (`is_healthy === true`).

- Domain defaults in admin/domain creation shell
  - Frontend form extension:
    - [`/data/home/tkodippili/Desktop/localTest_context_engine/client/src/components/settings/panels/KnowledgeGraphSettingsPanel.tsx`](/data/home/tkodippili/Desktop/localTest_context_engine/client/src/components/settings/panels/KnowledgeGraphSettingsPanel.tsx)
    - Add six retrieval-default fields in `Create domain` form and include them in create payload.
  - API client payload types:
    - [`/data/home/tkodippili/Desktop/localTest_context_engine/client/src/lib/api/knowledge-graph-admin.ts`](/data/home/tkodippili/Desktop/localTest_context_engine/client/src/lib/api/knowledge-graph-admin.ts)

- Backend domain model + persistence for retrieval defaults
  - [`/data/home/tkodippili/Desktop/localTest_context_engine/app/lightrag_deploy/models.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/lightrag_deploy/models.py)
  - [`/data/home/tkodippili/Desktop/localTest_context_engine/app/lightrag_deploy/service.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/lightrag_deploy/service.py)
  - [`/data/home/tkodippili/Desktop/localTest_context_engine/app/lightrag_deploy/compose.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/lightrag_deploy/compose.py)
  - [`/data/home/tkodippili/Desktop/localTest_context_engine/app/services/lightrag_domain_registry.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/services/lightrag_domain_registry.py)
  - Persist domain-level retrieval defaults in manifest/registry and include them in domain listing payload so chat can consume defaults.

- Chat defaults resolution
  - [`/data/home/tkodippili/Desktop/localTest_context_engine/client/src/stores/lightrag-domain-store.ts`](/data/home/tkodippili/Desktop/localTest_context_engine/client/src/stores/lightrag-domain-store.ts)
  - [`/data/home/tkodippili/Desktop/localTest_context_engine/client/src/components/chat/LightRagChatShell.tsx`](/data/home/tkodippili/Desktop/localTest_context_engine/client/src/components/chat/LightRagChatShell.tsx)
  - When a domain is selected, derive retrieval settings from that domain’s stored defaults, while keeping mode behavior intact.

- Upload route wiring (admin-only)
  - Reuse existing settings route navigation store in [`/data/home/tkodippili/Desktop/localTest_context_engine/client/src/stores/settings-dialog-store.ts`](/data/home/tkodippili/Desktop/localTest_context_engine/client/src/stores/settings-dialog-store.ts) and open the knowledge-graph admin surface from menu.
  - Keep backend security authoritative via existing admin guard on `/admin/*` routes.

## DESIGN.md Compliance Guardrails
- Follow [`/data/home/tkodippili/Desktop/localTest_context_engine/DESIGN.md`](/data/home/tkodippili/Desktop/localTest_context_engine/DESIGN.md):
  - `12px` for popup containers, `9999px` for interactive controls.
  - No shadows; use border/background separation only.
  - Grayscale-only styling and restrained typography weights.
  - Keep motion minimal (remove decorative transitions for this menu/popup).

## Verification
- UI checks:
  - Plus trigger + popup parity feels consistent with provided references.
  - Admin sees `Upload`; non-admin does not.
  - Retrieval entry opens inline selector-only panel.
- Behavior checks:
  - Retrieval selector only shows healthy deployed KGs.
  - New domain creation stores six retrieval defaults.
  - Chat requests use selected domain defaults without requiring user tuning.
- Tests:
  - Update/add frontend unit tests for menu visibility and domain filtering.
  - Update/add backend tests for create-domain defaults persistence and list-domain exposure.
  - Run targeted lint/tests on touched client/app modules before handoff.

## Risk Notes
- Existing chat stream endpoint (`/api/conversations/...`) is external to the FastAPI app in this repo; plan keeps compatibility by shaping client payload from selected domain defaults without changing the stream contract.