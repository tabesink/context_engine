# 01 Architecture Decision: Evidence Side Panel Boundary

## Decision

Use `context_engine` as the only backend API the WebUI calls for evidence retrieval.

The WebUI must not call LightRAG directly and must not depend on the raw LightRAG response shape.

## Backend Contract

The backend should expose an evidence-only retrieval endpoint:

```text
POST /retrieve
```

Request shape should match the existing retrieval request model:

```json
{
  "query": "string",
  "mode": "auto | semantic | navigation | hybrid",
  "document_ids": ["optional document ids"],
  "lightrag_domain_id": "optional selected domain id",
  "top_k": 8,
  "include_assets": true,
  "include_thumbnails": true,
  "max_assets": 5,
  "include_debug": false
}
```

Response shape should match the existing retrieval response model:

```json
{
  "query": "string",
  "mode": "hybrid",
  "evidence": [],
  "assets": [],
  "debug": null
}
```

## Why `/retrieve` Instead of More `/query/*`

The side panel needs evidence, not a generated answer.

A route named `/retrieve` communicates this clearly:

- `POST /retrieve` means evidence-only retrieval.
- `POST /query` or `/query/answer` means answer generation.
- The WebUI side panel should use `/retrieve`.

## Removed Query Routes

The current backend is retrieve-only for evidence reporting:

```text
POST /retrieve
```

The previous `/query/*` surface is removed, and tests assert `/query/retrieve` returns 404. Do not restore a compatibility alias as part of routine evidence-panel work. If a future client requires an alias, treat it as a separate product/API decision and keep it as a thin wrapper around `RetrievalService.retrieve(...)`.

## Ownership Boundary

| Concern | Owner |
|---|---|
| User auth | `context_engine` backend |
| User permissions | `context_engine` backend |
| Domain selection | `context_engine` backend and WebUI selection state |
| Domain validation | `context_engine` backend |
| Semantic retrieval | LightRAG via backend adapter |
| Navigation retrieval | `context_engine` local navigation engine |
| Hybrid merge/deduplication | `context_engine` retrieval layer |
| Evidence normalization | `context_engine` backend |
| Evidence rendering | WebUI |
| Evidence persistence | Not required for first implementation |

## Data Flow

```text
WebUI
  |
  | POST /retrieve
  v
context_engine API route
  |
  v
RetrievalService.retrieve()
  |
  +--> RoutingPolicy selects local/navigation/LightRAG strategy
  |
  +--> LightRAGRemoteRetrievalEngine for semantic evidence
  |
  +--> RichNavigationEngine for page/section/chunk evidence
  |
  +--> HybridMerger deduplicates and ranks
  |
  +--> Evidence mapper normalizes fields
  |
  +--> RetrievalAssetResolver attaches image/table assets if requested
  v
RetrieveResponse
  |
  v
WebUI right side panel
```

## Evidence Item Requirements

Every evidence item should be renderable as a card. Minimum card fields:

- stable evidence id
- source engine
- snippet text
- score if available
- document id
- source path or document title if available
- page start/end if available
- section title if available
- explicit chunk id/reference id if promoted by the backend
- metadata for raw optional source details

## Error Handling

The side panel should not silently show stale evidence.

Recommended behavior:

- On new retrieval start: clear previous panel or mark it loading.
- On success: replace panel evidence with the returned evidence.
- On 401/403: redirect or show auth error.
- On 400: show request/domain validation error.
- On 502/503: show LightRAG unavailable message.
- On empty evidence: show “No evidence found for this query.”

## Non-Goals

This change should not:

- add conversation storage
- add answer streaming
- add a new LightRAG client in the WebUI
- add a separate database table for evidence
- add an independent citation model unless needed later
- change document ingestion
- change LightRAG deployment
