# Re-review Summary

## Current implementation state

The repo now has the intended two-tab right panel structure in the client:

- `SidePanel.tsx` supports `Context Stream` and `Source Navigator` tabs.
- `LightRagChatShell.tsx` switches to `source-navigator` when the user clicks a workspace-tree node and switches to `context-stream` when chat retrieval returns context.
- `WorkspaceTree.tsx` passes the selected node through the chat shell.
- `workspace-context.ts` calls `GET /lightrag/domains/{domain_id}/workspace-context?node_id=...`.

The backend already has both workspace-tree and workspace-context endpoints. The workspace context schema and service already return `assets` with `url`, `thumbnail_url`, `asset_type`, `caption`, `page_number`, and metadata.

## Gap

The data contract is mostly present, but the UI is still text-first:

- Retrieved response assets are not converted into right-panel cards.
- Source Navigator assets are not rendered as proper figure/table cards.
- The existing table/figure context item placeholders should become real UI components.

## Implementation direction

Add a reusable `AssetCards.tsx` component and use it in both tabs:

- `FigureCard`: one large image/figure card.
- `TableCard`: compact card for each table asset.

The retrieval adapter should append one primary figure item and all table items to `message.contextItems`, so Context Stream naturally displays retrieval assets.

The Source Navigator should split `WorkspaceSourceContext.assets` into:

- first figure/image asset → one `FigureCard`
- table assets → multiple `TableCard`s
- optional fallback assets → compact table-style cards or generic rows
