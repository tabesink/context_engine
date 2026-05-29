# Frontend Patch Guide

## Files

```text
client/src/components/settings/panels/KnowledgeGraphSettingsPanel.tsx
client/src/components/settings/lightrag-domains/CreateDomainForm.tsx
client/src/components/settings/lightrag-domains/DomainLifecycleCard.tsx
client/src/lib/api/knowledge-graph-admin.ts
client/src/types/lightrag.ts
```

## CreateDomainForm

Remove:

```text
Advanced retrieval defaults section
retrieval profile preset selector
all top_k/token budget inputs
```

Keep only:

```text
Domain ID
Display name
Embedding model
Host port auto/custom
Create button
```

## KnowledgeGraphSettingsPanel

Remove create payload fields:

```ts
start: true,
top_k,
chunk_top_k,
chunk_rerank_top_k,
max_token_for_text_unit,
max_token_for_global_context,
max_token_for_local_context,
```

Remove purge state/handlers:

```ts
purgePreviewByDomain
runPreviewPurge
runAction(domainId, "purge")
```

Remove advanced action handler:

```ts
runAdvancedAction(domainId, "recreate" | "regenerate")
```

Update create success notice:

```text
Domain created. Click Start when ready.
```

## DomainLifecycleCard

Remove menu items/buttons:

```text
Repair
Recreate container
Regenerate config
Preview purge
Purge permanently
```

Keep lifecycle buttons:

```text
Start
Stop
Delete
```

Suggested delete confirmation copy:

```text
Delete domain?
This removes the LightRAG runtime from active use and archives runtime files. Local document records are preserved.
```

## API client

Remove methods:

```ts
repair()
recreate()
regenerate()
purgePreview()
purge()
```

Keep methods:

```ts
list()
create()
up()
down()
remove() // optionally rename to deleteDomain()
```
