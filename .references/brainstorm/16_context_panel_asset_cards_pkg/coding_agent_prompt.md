# Coding Agent Prompt

You are modifying `tabesink/context_engine` after the two-tab right context panel has already been implemented.

## Goal

Implement image/figure and table display in the right-hand context panel for both tabs:

1. **Context Stream**: display retrieved chat context, including one primary figure card and table cards from `RetrieveResponse.assets`.
2. **Source Navigator**: display exact source context from clicked workspace-tree nodes, including one primary figure card and table cards from `WorkspaceSourceContext.assets`.

## Design constraints

Follow `DESIGN.md`:

- pure white / snow surfaces
- grayscale only
- no chromatic color
- 12px rounded cards
- thin gray borders
- no shadows
- pill-shaped metadata badges
- compact but readable right-panel density

## Implementation tasks

1. Add `client/src/components/chat/AssetCards.tsx` from this package.
2. Replace `client/src/lib/retrieve-response-adapter.ts` with the provided implementation.
3. Extend `ContextPanelItem` in `client/src/types/chat.ts` with asset URL/caption/type fields from `patches/chat-types-additions.patch`.
4. Update `client/src/components/chat/SidePanel.tsx` using `patches/side-panel-integration-notes.md`.
5. Run TypeScript checks and lint.
6. Manually test:
   - Ask a query that returns evidence and assets.
   - Confirm Context Stream shows text evidence, one figure card, and table cards.
   - Click a workspace-tree figure/table/source node.
   - Confirm Source Navigator shows exact source text and asset cards.

## Important rule

Do not make the frontend call LightRAG directly. The right panel must use Context Engine API responses only.

## Acceptance criteria

- No duplicate right-panel state system is introduced.
- Source Navigator remains deterministic: clicking a tree node does not trigger retrieval.
- Context Stream remains retrieval-driven.
- Figure preview works with bearer-token-protected asset endpoints by fetching the image as a blob.
- Tables degrade gracefully if only a caption/text preview is available.
