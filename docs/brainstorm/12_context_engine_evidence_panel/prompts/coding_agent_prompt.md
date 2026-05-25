# Coding Agent Prompt: Implement Evidence Side Panel Backend Contract

You are a senior backend/frontend engineer working in `context_engine`.

## Goal

Extend the backend and WebUI contract so retrieved evidence can be displayed in a right-hand side panel.

## Important Constraints

- Do not import the `easy-deploy-lightrag` backend wrapper.
- Do not add duplicate auth routes.
- Do not add a second retrieval pipeline.
- Do not call LightRAG directly from the WebUI.
- Reuse the existing `RetrievalService.retrieve(...)` flow.
- Reuse existing `RetrieveRequest`, `RetrieveResponse`, `EvidenceResponse`, and `AssetResponse` where possible.
- Use the existing clean top-level `POST /retrieve` endpoint.
- Keep removed `/query/*` routes removed unless the user explicitly asks for a new compatibility API decision.
- Use vertical TDD slices: one behavior test, minimal implementation, then repeat.

## Repository Areas to Inspect First

Inspect these files before editing:

```text
app/main.py
app/api/routes/retrieve.py
app/schemas/retrieval.py
app/services/retrieval_service.py
app/retrieval/evidence_mapper.py
app/retrieval/lightrag_remote_engine.py
app/integrations/lightrag_remote_adapter.py
app/retrieval/rich_navigation_engine.py
app/retrieval/hybrid_merger.py
```

## Backend Tasks

1. Confirm `POST /retrieve` exists.
2. Keep it a thin wrapper around `RetrievalService(session).retrieve(...)`.
3. Ensure it requires existing authenticated user behavior.
4. Ensure it returns `RetrieveResponse`.
5. Preserve removed `/query/*` route behavior unless a separate API decision changes it.
6. If needed, add explicit evidence display fields:
   - `source_path`
   - `document_title`
   - `chunk_id`
   - `reference_id`
7. Update evidence mapper only if fields are added.
8. Do not persist evidence.

## WebUI Tasks

1. Add or update right-hand side evidence panel.
2. On query submit, call `POST /retrieve` with selected domain, document filters, and `include_assets` as needed.
3. Render evidence cards using backend order.
4. Support loading, empty, success, and error states.
5. Render assets if present.
6. Do not parse raw LightRAG response.

## Required Tests

Add or update tests for:

- `/retrieve` requires auth.
- `/retrieve` returns evidence response.
- removed `/query/retrieve` returns 404 if the endpoint boundary is touched.
- `include_debug` only returns debug for admin.
- domain/document mismatch returns 400.
- empty evidence returns 200 with `evidence: []`.
- WebUI panel states: loading, success, empty, error.

Add these tests one at a time. For each slice, write one failing public behavior test, make the minimal implementation change, run the targeted test, then continue.

## Acceptance Criteria

- `python -m pytest -q` passes.
- `/retrieve` is available in OpenAPI.
- `/query/retrieve` remains removed unless explicitly restored by a separate decision.
- WebUI displays evidence in the right side panel.
- No duplicate retrieval pipeline added.
- No direct WebUI-to-LightRAG calls added.
- No unrelated refactor included.

## Expected API Contract

Request:

```json
{
  "query": "What does the policy say about service calls?",
  "mode": "hybrid",
  "lightrag_domain_id": "default",
  "document_ids": null,
  "top_k": 8,
  "include_assets": true,
  "include_thumbnails": true,
  "max_assets": 5,
  "include_debug": false
}
```

Response:

```json
{
  "query": "What does the policy say about service calls?",
  "mode": "hybrid",
  "evidence": [
    {
      "evidence_id": "...",
      "document_id": "...",
      "source_engine": "lightrag",
      "text": "...",
      "score": 0.87,
      "page_start": 4,
      "page_end": 4,
      "section_title": "Service Calls",
      "source_path": "policy.pdf",
      "document_title": "Policy",
      "chunk_id": "...",
      "reference_id": "...",
      "metadata": {}
    }
  ],
  "assets": [],
  "debug": null
}
```
