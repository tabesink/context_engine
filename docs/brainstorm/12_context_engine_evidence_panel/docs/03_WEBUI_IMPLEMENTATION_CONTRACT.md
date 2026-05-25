# 03 WebUI Implementation Contract

## Goal

The WebUI should display retrieved evidence in a right-hand side panel.

The panel should be driven by backend `RetrieveResponse`, not by raw LightRAG data.

## API Call

Canonical endpoint:

```text
POST /retrieve
```

Removed endpoint:

```text
POST /query/retrieve
```

Do not call removed `/query/*` routes from the evidence panel.

## Request Example

```json
{
  "query": "What does the document say about service calls?",
  "mode": "hybrid",
  "lightrag_domain_id": "ablemed",
  "document_ids": null,
  "top_k": 8,
  "include_assets": true,
  "include_thumbnails": true,
  "max_assets": 5,
  "include_debug": false
}
```

## Response Example

```json
{
  "query": "What does the document say about service calls?",
  "mode": "hybrid",
  "evidence": [
    {
      "evidence_id": "navigation:doc-1:chunk:section-3-001",
      "document_id": "doc-1",
      "source_engine": "navigation",
      "text": "Service calls are billed separately after the initial labor warranty period...",
      "score": 2.82,
      "page_start": 6,
      "page_end": 6,
      "section_title": "Service Calls",
      "source_path": "Warranty Policy.pdf",
      "document_title": "Warranty Policy",
      "chunk_id": "section-3-001",
      "reference_id": null,
      "metadata": {
        "source": "source_chunk"
      }
    }
  ],
  "assets": [
    {
      "asset_id": "asset-1",
      "document_id": "doc-1",
      "asset_type": "image",
      "caption": "Warranty service table",
      "page_number": 6,
      "url": "/documents/doc-1/assets/asset-1",
      "thumbnail_url": "/documents/doc-1/assets/asset-1/thumbnail"
    }
  ],
  "debug": null
}
```

## WebUI State Model

Recommended local state:

```ts
type EvidencePanelState = {
  status: "idle" | "loading" | "success" | "empty" | "error";
  query: string;
  evidence: EvidenceItem[];
  assets: EvidenceAsset[];
  selectedEvidenceId?: string;
  errorMessage?: string;
};
```

## Evidence Item Type

```ts
type EvidenceItem = {
  evidence_id: string;
  document_id: string;
  source_engine: "lightrag" | "navigation" | string;
  text: string;
  score?: number | null;
  page_start?: number | null;
  page_end?: number | null;
  section_title?: string | null;
  source_path?: string | null;
  document_title?: string | null;
  chunk_id?: string | null;
  reference_id?: string | null;
  metadata: Record<string, unknown>;
};
```

## Asset Type

```ts
type EvidenceAsset = {
  asset_id: string;
  document_id: string;
  asset_type: "image" | "table" | "figure" | string;
  caption?: string | null;
  page_number?: number | null;
  url: string;
  thumbnail_url?: string | null;
};
```

## Panel Behavior

### Loading

When the user submits a new query:

- clear selected evidence
- set state to `loading`
- optionally keep old evidence dimmed with a “refreshing” indicator, but do not mix old and new evidence

### Success

When evidence returns:

- if `evidence.length > 0`, show evidence cards
- if `evidence.length === 0`, show empty-state message
- show assets in the relevant evidence card if asset IDs can be matched through metadata

### Error

Show a readable error:

| Backend status | Panel message |
|---:|---|
| 401 | “Please sign in again.” |
| 403 | “You do not have access to this retrieval scope.” |
| 400 | Use backend error detail if safe. |
| 502 | “The retrieval engine returned an invalid response.” |
| 503 | “The retrieval engine is unavailable.” |

## Evidence Card Layout

Each card should show:

```text
[Source engine badge] [score if available]
Document title or source_path
Section title
Page range
Snippet text
Open source / page button
Assets preview if available
```

Example:

```text
LightRAG · score 0.87
Warranty Policy.pdf
Section: Service Calls · Page 6

Service calls are billed separately after the initial labor warranty period...

[Open page] [Copy citation]
```

## Sorting

Use backend order as the source of truth. The backend already merges/deduplicates and ranks.

Do not re-rank in the WebUI for the first version.

## Domain Selection

The WebUI should send `lightrag_domain_id` from the selected domain.

If no domain is selected:

- send `null` only if backend default domain behavior is acceptable
- otherwise require explicit domain selection in UI

## Document Filters

If the user selected specific documents, send `document_ids`.

If the selected documents do not belong to the selected domain, backend should return 400. The WebUI should show the message and ask the user to adjust selection.

## Accessibility

- Right panel should be keyboard navigable.
- Evidence cards should have semantic headings.
- Long snippets should be expandable.
- Side panel should be collapsible.
- Selected evidence should have visible focus state.

## First Version UI Scope

Build only:

- evidence list
- empty state
- loading state
- error state
- basic asset thumbnails
- open source/page hook if existing document page API exists

Do not build:

- inline PDF viewer
- graph view
- persistent evidence history
- evidence annotations
- reranking controls
