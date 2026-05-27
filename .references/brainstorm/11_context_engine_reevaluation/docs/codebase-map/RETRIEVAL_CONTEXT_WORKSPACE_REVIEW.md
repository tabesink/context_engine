# Retrieval, Context Panel, and Workspace Tree Review

## Desired Flow

```text
Authenticated user types a question
  → frontend sends request to /retrieve
  → request includes selected LightRAG domain
  → backend validates user and domain
  → LightRAG semantic retrieval runs
  → local metadata enrichment runs
  → backend returns stable evidence response
  → frontend maps evidence to context panel items
  → frontend updates or fetches workspace tree
```

## Current Positive Findings

The modified codebase appears to include:

- `/retrieve` route
- user-accessible retrieval, not admin-only
- retrieval service
- LightRAG remote retrieval engine
- local navigation retrieval engine
- evidence mapper
- optional asset resolver
- workspace-tree backend route
- workspace-tree service
- chat frontend using `/retrieve`
- right-side panel and workspace tree components

## Main Gap

The frontend retrieval client appears to convert evidence into assistant message text, but does not yet route structured evidence into:

- `contextItems`
- `sourceTree`
- side panel asset cards
- workspace tree updates

## Recommended Frontend Mapping

After `/retrieve` returns:

```ts
const response = await retrieve(...);

const contextItems = response.evidence.map((e, index) => ({
  id: e.reference_id ?? e.evidence_id ?? `E${index + 1}`,
  title: e.document_title ?? e.source_path ?? "Source",
  excerpt: e.text,
  sourcePath: e.source_path,
  documentId: e.document_id,
  chunkId: e.chunk_id,
  pageNumber: e.page_number ?? e.page_start,
  score: e.score,
  assets: assetsForEvidence(e, response.assets),
}));
```

Then call:

```ts
onContext(contextItems, sourceTree);
```

or update the relevant chat state/store.

## Recommended Backend Evidence Contract

Stable top-level evidence fields:

```text
reference_id
document_id
document_title
source_path
chunk_id
section_id
section_title
page_number
page_start
page_end
score
text
metadata
assets
```

It is acceptable to keep assets as a separate response-level array, but frontend mapping must be documented and tested.

## Workspace Tree Strategy

Simplest approach:

1. On chat domain selection:
   - fetch `/lightrag/domains/{domain_id}/workspace-tree`
2. After upload/reingestion success:
   - refetch tree
3. After retrieval:
   - optionally highlight evidence-linked nodes

Tree shape:

```text
Workspace
  → Domain
      → Document
          → Section
              → Page
              → Chunk
              → Asset
```

## Required Tests

Backend:

- regular user can call `/retrieve`
- regular user can call workspace-tree endpoint
- `/retrieve` returns evidence with document/source/chunk fields
- include_assets returns assets when available
- retrieval fails clearly if domain unavailable

Frontend:

- chat calls `/retrieve`
- selected domain is passed
- evidence becomes context panel items
- empty evidence renders gracefully
- workspace tree loads for selected domain
- evidence source can link or highlight tree/document node
