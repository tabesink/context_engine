# Phase 1 — Frontend UI Simplification

## Goal

Make the UI show only the lean lifecycle.

```text
Create
Start
Stop
Delete
```

## Files likely affected

```text
client/src/components/settings/panels/KnowledgeGraphSettingsPanel.tsx
client/src/components/settings/lightrag-domains/CreateDomainForm.tsx
client/src/components/settings/lightrag-domains/DomainLifecycleCard.tsx
client/src/lib/api/knowledge-graph-admin.ts
client/src/types/lightrag.ts
```

## Remove from CreateDomainForm

Remove:

```text
Advanced retrieval defaults
retrieval preset selector
top_k
chunk_top_k
chunk_rerank_top_k
max_token_for_text_unit
max_token_for_global_context
max_token_for_local_context
```

Keep:

```text
domain ID
display name
embedding model
host port auto/custom
```

## Remove from domain card

Remove actions:

```text
Repair
Recreate container
Regenerate config
Preview purge
Purge permanently
```

Keep actions:

```text
Start
Stop
Delete
```

Non-lifecycle actions may remain if product wants them:

```text
Upload document
View documents
Event tail
```

But visually separate them from lifecycle controls.

## Change create payload

Remove:

```ts
start: true
retrieval default fields
```

## Change create success message

Use:

```text
Domain created. Click Start when ready.
```

## Acceptance criteria

- No advanced retrieval defaults in create UI.
- No repair/recreate/regenerate/purge UI items.
- Create does not send `start: true`.
- Create does not send retrieval defaults.
- UI still allows domain creation, start, stop, delete.
