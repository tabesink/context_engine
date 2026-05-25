# 04 Test Plan

## Goal

Protect the new evidence panel backend contract and prevent route/API drift.

## Backend Unit Tests

### 1. `/retrieve` requires authentication

Expected:

- unauthenticated request returns 401 or existing auth failure status
- no retrieval service call is made

Suggested test name:

```text
test_retrieve_requires_auth
```

### 2. `/retrieve` returns evidence response

Mock or seed retrieval evidence.

Expected response:

```json
{
  "query": "...",
  "mode": "hybrid",
  "evidence": [...],
  "assets": [],
  "debug": null
}
```

Suggested test name:

```text
test_retrieve_returns_evidence_items
```

### 3. Removed `/query/*` routes stay removed

Call removed query endpoints with an authenticated request.

Expected:

- `/query` returns 404
- `/query/answer` returns 404
- `/query/retrieve` returns 404
- evidence-panel work does not silently restore a second API surface

Suggested test name:

```text
test_removed_query_routes_return_404
```

### 4. Debug is admin-only

Existing service behavior should only include debug when:

```text
request.include_debug == true and user.role == "admin"
```

Expected:

- normal user gets `debug: null`
- admin gets debug if requested

Suggested test names:

```text
test_retrieve_hides_debug_for_normal_user
test_retrieve_includes_debug_for_admin_when_requested
```

### 5. Domain/document mismatch returns 400

Create or mock document metadata with LightRAG domain A.

Request with `lightrag_domain_id = B` and that document id.

Expected:

- 400
- error explains selected documents must belong to selected domain

Suggested test name:

```text
test_retrieve_rejects_document_filter_from_wrong_lightrag_domain
```

### 6. Evidence mapper exposes display fields

If adding explicit fields such as `source_path`, `chunk_id`, or `reference_id`, test the mapper.

Suggested test name:

```text
test_evidence_mapper_projects_display_metadata
```

### 7. Empty evidence returns 200

Expected:

- 200
- `evidence: []`
- `assets: []`

Suggested test name:

```text
test_retrieve_empty_evidence_is_successful_empty_result
```

## LightRAG Adapter Tests

### 1. Maps chunk metadata to evidence

Given LightRAG `/query/data` response with:

```json
{
  "data": {
    "chunks": [
      {
        "chunk_id": "c1",
        "content": "...",
        "score": 0.9,
        "metadata": {
          "document_id": "doc-1",
          "page_start": 2,
          "page_end": 3
        }
      }
    ],
    "references": []
  }
}
```

Expected:

- evidence id maps from chunk id
- page refs are preserved
- metadata is preserved

### 2. Invalid LightRAG response maps to backend error

Expected:

- adapter raises `LightRAGInvalidResponse`
- API returns 502

### 3. LightRAG unavailable maps to 503

Expected:

- connection/timeout raises `LightRAGServiceUnavailable`
- API returns 503

## WebUI Tests

### 1. Evidence panel loading state

When query is submitted:

- panel state becomes loading
- old selected evidence is cleared

### 2. Evidence cards render fields

Given response evidence:

- source engine badge appears
- snippet appears
- section/page appears when provided
- score appears when provided

### 3. Empty evidence state

Given `evidence: []`:

- panel shows “No evidence found” or equivalent

### 4. Error state

Given backend error:

- panel shows readable error
- old evidence is not presented as fresh

### 5. Asset rendering

Given `assets[]`:

- thumbnail is displayed if `thumbnail_url` exists
- full asset link uses `url`

## Contract Test Example

Use this fixture to lock the response shape:

```json
{
  "query": "service calls",
  "mode": "hybrid",
  "evidence": [
    {
      "evidence_id": "navigation:doc-1:chunk:c1",
      "document_id": "doc-1",
      "source_engine": "navigation",
      "text": "Service calls are billed separately.",
      "score": 2.75,
      "page_start": 4,
      "page_end": 4,
      "section_title": "Service Calls",
      "source_path": "warranty.pdf",
      "document_title": "Warranty Policy",
      "chunk_id": "c1",
      "reference_id": null,
      "metadata": {"source": "source_chunk"}
    }
  ],
  "assets": [],
  "debug": null
}
```

## Required Test Command

```bash
python -m pytest -q
```

## Definition of Done

- `/retrieve` works for authenticated users.
- `/query/retrieve` remains removed unless a separate API decision restores it.
- Response contract is stable.
- WebUI panel renders success, loading, empty, and error states.
- No duplicate retrieval pipeline added.
- No direct WebUI-to-LightRAG call added.
