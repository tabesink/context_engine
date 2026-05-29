# Patch 0004 — Right-panel split follow-up outline

Do this after 0001-0003 compile.

## Goal

Keep one right-panel shell and split content into two views:

- `ContextStreamView`
- `SourceNavigatorView`

Do not create a second side panel.

## Minimal frontend changes

1. `WorkspaceTree.tsx`
   - Add prop: `onSelectNode?: (nodeId: string) => void`.
   - Attach it to `TreeItemLabel`/row click.
   - Do not call retrieval.
   - Do not mutate retrieval settings.

2. `chat-session-store.ts`
   - Add:
     - `activePanelTab: "context-stream" | "source-navigator"`
     - `selectedSourceNodeId?: string`
     - `sourceContext?: WorkspaceSourceContext`
     - `sourceContextStatus: "idle" | "loading" | "ready" | "error"`
     - `sourceContextError?: string`

3. `LightRagChatShell.tsx`
   - Add `handleSourceNodeSelect(nodeId)`:
     - set active tab to `source-navigator`
     - set selected source node id
     - call `fetchWorkspaceSourceContext(domainId, nodeId)`
     - update source context state
   - Pass `onSelectNode` to `WorkspaceTree`.
   - Pass active tab and source context props to `SidePanel`.

4. `SidePanel.tsx`
   - Keep resize/overlay behavior.
   - Add two tabs in the header:
     - Context Stream
     - Source Navigator
   - Move current context list into `ContextStreamView`.
   - Add `SourceNavigatorView` for exact source context.
   - Use shared `AssetCards` for any figure/table/image/table assets.

5. `AssetCards.tsx`
   - Accept `assets: VisualAsset[]`.
   - Render one visual grammar for both table and figure cards.
   - Follow `DESIGN.md`: flat grayscale, no shadows, restrained border, 12px non-interactive radius, pill-shaped interactive links/buttons.

## Acceptance checks

- Clicking a tree node changes only Source Navigator state.
- Retrieval settings remain unchanged.
- Context Stream keeps selected assistant response behavior.
- Source Navigator shows exact source text and assets.
- No direct LightRAG frontend calls are introduced.
