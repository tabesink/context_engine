# Retrieval, Chat, and Evidence Review

## Backend Retrieval Strengths

Backend `/retrieve` already has the right shape for a canonical Context Engine evidence API.

Observed request/response concepts include:

```text
RetrieveRequest
  query
  mode
  document_ids
  lightrag_domain_id
  top_k
  include_assets
  include_thumbnails

RetrieveResponse
  query
  mode
  evidence
  assets
  debug

EvidenceResponse
  evidence_id
  document_id
  source_engine
  text
  score
  page_start/page_end
  section_title
  source_path
  document_title
  chunk_id
  reference_id
  metadata
```

This is very close to what the context panel needs.

## Frontend Contract Gap

The frontend chat shell appears to use a streaming contract with events:

```text
metadata
context
progress
token
done
error
```

and frontend context-panel item types like:

```text
ContextPanelItem
  id
  kind
  title
  content
  page_start/page_end
  section_path
  file_path
  chunk_id
  source_type
  handles
```

This is not the same as backend `RetrieveResponse`.

## Required Decision

Choose one of two simple options:

### Option A: Make chat call `/retrieve` directly

Simpler and lower entropy.

```text
Chat submit
  → POST /retrieve
  → map RetrieveResponse.evidence/assets to chat answer + context panel
```

Use this if streaming answer generation is not required yet.

### Option B: Keep streaming but make it wrap RetrievalService

```text
Chat submit
  → POST /chat/stream
  → internally calls RetrievalService
  → emits metadata/context/progress/token/done events
```

Use this only if streaming UX is required.

Do not let frontend call LightRAG directly or maintain a separate LightRAG query mental model.

## Recommended Evidence Contract

Backend should return or expose enough fields for:

```text
reference_id
document_id
document_title
source_path
chunk_id
section_id
section_title
page_number or page_start/page_end
score
text
metadata
assets
```

Current backend evidence mostly supports this already. Add `section_id` and normalized `page_number` if needed by the UI.

## Retrieval Permissions

Required behavior:

```text
Regular authenticated user
  → can call /retrieve
  → can retrieve from ready shared domains
  → cannot upload/configure/manage domains/providers
```

## Domain Selection

Frontend should pass stable domain ID, not only port.

Avoid using port as primary frontend domain identity. Port is deployment detail. Domain ID is product identity.

## Required Tests

- regular user can call `/retrieve`
- unauthenticated user cannot
- selected domain is required or backend default is explicit
- invalid domain fails clearly
- evidence includes stable document/source fields
- assets can be included or omitted safely
- frontend maps backend evidence to context panel items
