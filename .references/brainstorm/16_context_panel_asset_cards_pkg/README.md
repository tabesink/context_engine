# Context Panel Asset Cards Implementation Package

This package implements the next step for the two-tab right-hand panel:

- **Context Stream** shows retrieved evidence plus one primary figure card and compact table cards from chat retrieval assets.
- **Source Navigator** shows exact source text plus one primary figure card and compact table cards from clicked workspace-tree/source assets.

The UI follows `DESIGN.md`: grayscale-only, pure white/snow surfaces, 12px rounded cards, thin borders, no shadows, pill metadata, and restrained density.

## Package contents

```text
files/
  client/src/components/chat/AssetCards.tsx
  client/src/lib/retrieve-response-adapter.ts
patches/
  chat-types-additions.patch
  side-panel-integration-notes.md
  retrieval-adapter-replacement-notes.md
review.md
coding_agent_prompt.md
junior_dev_checklist.md
```

## What to apply

1. Add the new component:

```text
client/src/components/chat/AssetCards.tsx
```

2. Replace:

```text
client/src/lib/retrieve-response-adapter.ts
```

with the implementation in this package.

3. Add the type fields from:

```text
patches/chat-types-additions.patch
```

4. Update `client/src/components/chat/SidePanel.tsx` using:

```text
patches/side-panel-integration-notes.md
```

## Design rule

Do not display every figure returned by retrieval. The right panel should show **one primary figure card** and **multiple table cards**. This keeps the panel scannable and consistent with the lightweight Context Engine visual language.
