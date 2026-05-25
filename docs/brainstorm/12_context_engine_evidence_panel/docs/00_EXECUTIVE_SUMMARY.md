# 00 Executive Summary

## Goal

Extend `context_engine` so the WebUI can display retrieved evidence in a right-hand side panel.

The desired user experience is:

```text
User asks a question
  -> WebUI sends retrieval request to context_engine
  -> context_engine retrieves evidence from the selected LightRAG domain and/or navigation index
  -> WebUI renders answer/chat in the main pane
  -> WebUI renders evidence cards in the right-hand side panel
```

## Current Backend Foundation

The current repository already contains most of what is needed:

- `app/api/routes/retrieve.py` exposes `POST /retrieve`.
- `app/schemas/retrieval.py` defines `RetrieveRequest`, `EvidenceResponse`, `AssetResponse`, and `RetrieveResponse`.
- `app/services/retrieval_service.py` builds `RetrieveResponse` from retrieved evidence and optional assets.
- `app/retrieval/lightrag_remote_engine.py` delegates semantic retrieval to LightRAG.
- `app/integrations/lightrag_remote_adapter.py` calls LightRAG and maps returned chunks/references into internal `Evidence` objects.
- `app/retrieval/rich_navigation_engine.py` returns local navigation evidence from persisted document structure.
- `app/retrieval/hybrid_merger.py` deduplicates semantic and navigation evidence.
- `tests/test_api.py` asserts removed `/query/*` routes, including `/query/retrieve`, return 404.

## Recommended Shape

Use the top-level evidence-only route:

```text
POST /retrieve
```

This route returns the normalized `RetrieveResponse` shape used by the right-hand evidence panel.

Do not restore `/query/retrieve` as compatibility work unless that becomes a deliberate product decision. The current backend direction is retrieve-first and retrieve-only.

## Why This Is Clean

The WebUI does not need to know how LightRAG works. It only needs a stable evidence contract.

The backend remains the owner of:

- auth
- domain validation
- document filter validation
- LightRAG adapter calls
- local navigation evidence
- hybrid evidence merge
- asset URL resolution
- debug visibility rules

The WebUI owns:

- layout
- evidence panel open/close behavior
- evidence card rendering
- source/page/asset links
- selected evidence highlighting

## What Must Not Be Added

Do not add another query pipeline.
Do not add another answer route.
Do not import the `easy-deploy-lightrag` backend wrapper.
Do not call LightRAG directly from WebUI.
Do not make the side panel depend on raw LightRAG responses.

## Target Result

After implementation, the right-hand side panel can render evidence cards using:

```json
{
  "query": "What does the document say about warranty labor?",
  "mode": "hybrid",
  "evidence": [
    {
      "evidence_id": "lightrag:chunk:abc123",
      "document_id": "...",
      "source_engine": "lightrag",
      "text": "...",
      "score": 0.87,
      "page_start": 4,
      "page_end": 5,
      "section_title": "Warranty and Service",
      "source_path": "warranty_policy.pdf",
      "document_title": "Warranty Policy",
      "chunk_id": "abc123",
      "reference_id": "ref-7",
      "metadata": {
        "source": "source_chunk"
      }
    }
  ],
  "assets": [],
  "debug": null
}
```
