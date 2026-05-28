# UI Surface Map (Phase 0)

This map captures current UI/backend surface boundaries before larger phase work.

## Frontend Route + Component Map

- `/chat`
  - Entry: `client/src/app/chat/page.tsx`
  - Shell: `client/src/components/chat/LightRagChatShell.tsx`
  - Sub-surfaces:
    - Workspace tree: `components/chat/WorkspaceTree.tsx`
    - Retrieval context panel: `components/chat/SidePanel.tsx`
    - Conversation: `components/chat/ConversationView.tsx`
    - Composer: `components/chat/ChatComposer.tsx`
- Settings dialog (overlay, route-like internal sections)
  - Entry: `client/src/components/settings/SettingsDialog.tsx`
  - Shell composition (shadcn block aligned):
    - `client/src/components/ui/sidebar.tsx`
    - `client/src/components/ui/breadcrumb.tsx`
    - `client/src/components/ui/separator.tsx`
  - Sections:
    - `account` -> `panels/AccountSettingsPanel.tsx`
    - `provider` -> `panels/AIModelSettingsPanel.tsx` (Option C2 flat layout; `ProviderIcon` for OpenAI/AWS/Ollama)
    - `lightrag-domains` -> `panels/KnowledgeGraphSettingsPanel.tsx`
    - `documents` -> `panels/DocumentsProcessingSettingsPanel.tsx`
    - `jobs` -> placeholder (phase 5 target)
    - `system` -> placeholder (future admin controls)
- Global shell/navigation
  - `client/src/components/layout/AppPageFrame.tsx`
  - `client/src/components/layout/AppLayout.tsx`

## API Client Surface Map

- Domain/user-safe LightRAG
  - `client/src/lib/lightrag-client.ts`
  - `client/src/api/lightrag.ts`
  - `client/src/api/workspace-tree.ts`
  - `client/src/api/workspace-context.ts`
- Admin LightRAG lifecycle
  - `client/src/lib/api/knowledge-graph-admin.ts`
- Processing status
  - `client/src/api/processing-status.ts`
  - Hook consumer: `client/src/hooks/use-processing-status.ts`
- Documents + logs
  - `client/src/lib/api/admin-documents.ts`
- Auth/settings/users/retrieve
  - `client/src/lib/api/auth.ts`
  - `client/src/lib/api/ai-settings.ts`
  - `client/src/lib/api/users.ts`
  - `client/src/lib/api/retrieve.ts`

## State Store Map (Ownership Boundaries)

- Auth/session boundary
  - `client/src/stores/auth-store.ts`
- Settings dialog route/open boundary
  - `client/src/stores/settings-dialog-store.ts`
- Chat session + side-panel selection boundary
  - `client/src/stores/chat-session-store.ts`
- LightRAG domain selection boundary
  - `client/src/stores/lightrag-domain-store.ts`
- Graph visualization/query settings boundary
  - `client/src/stores/graph.ts`
  - `client/src/stores/settings.ts`

## Design Control Notes

- Settings controls use **`rounded-md`** per [DESIGN.md](../DESIGN.md) Radius and Shape — not pill-default overrides.
- Shared class tokens: `client/src/components/settings/settings-controls.ts`
- Provider brand icons: `client/src/components/icons/ProviderIcon.tsx`

## Reuse + Duplication Notes

- Repeated rounded panel/status/header patterns exist across:
  - `KnowledgeGraphSettingsPanel`
  - `GeneralSettingsPanel`
  - Chat shell status/header rows
- Lifecycle and document admin surfaces now use block-composed structures with local feature wiring:
  - lifecycle action strip + danger zone + advanced disclosure
  - documents overview counters + processing table + failure detail expansion
- Existing behavior should remain in current feature components; only shared presentation primitives should centralize repeated visual structure.

## Proposed Phase-0 Primitives

- `client/src/components/surfaces/StatusChip.tsx`
- `client/src/components/surfaces/PanelState.tsx`
- `client/src/components/surfaces/SectionCard.tsx`
- `client/src/components/surfaces/SurfaceHeader.tsx`

## Phase Attachment Points (1-7)

- Phase 1 (settings shell prep):
  - `SettingsDialog` + settings panels can adopt shared `SurfaceHeader`/`SectionCard`.
- Phase 2 (status API wiring):
  - `use-processing-status` and `api/processing-status` already provide an integration seam.
- Phase 3 (admin domain lifecycle UI):
  - `KnowledgeGraphSettingsPanel` is current anchor for decomposition.
- Phase 4 (document processing status UI):
  - `DocumentsProcessingSettingsPanel` + `api/processing-status` domain documents list endpoint.
- Phase 5 (job queue + event log):
  - admin logs surface in knowledge-graph panel can split into dedicated job/event views.
- Phase 6 (user-safe workspace/domain status):
  - chat header status row in `LightRagChatShell` is current user-facing anchor.
- Phase 7 (hardening):
  - consolidate panel/status presentation via `components/surfaces/*` and remove duplicated wrappers.
