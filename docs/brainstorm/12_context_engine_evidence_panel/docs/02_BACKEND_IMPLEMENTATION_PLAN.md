# 02 Backend Implementation Plan

## Implementation Summary

Extend the existing evidence-only API contract for the right-hand evidence panel while reusing the current retrieval service and response models.

Current baseline:

```text
app/api/routes/retrieve.py        # existing thin route module
app/main.py                       # already includes the retrieve router
app/schemas/retrieval.py          # current retrieval response contract
app/retrieval/evidence_mapper.py  # maps domain evidence to API evidence
app/services/retrieval_service.py # owns retrieval orchestration, assets, logging, and debug visibility
```

## Step 1: Confirm Current Route Registration Is Still Thin

Inspect `app/main.py` and route registration.

Expected current state:

```text
app.include_router(retrieve.router)
```

Then inspect `app/api/routes/retrieve.py`. The route should remain a thin wrapper:

```python
return RetrievalService(session).retrieve(request=request, user=user)
```

Do not add retrieval logic to the route.

## Step 2: Preserve Top-Level `/retrieve`

Canonical endpoint:

```text
POST /retrieve
```

The current implementation already follows the intended route shape:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.schemas.retrieval import RetrieveRequest, RetrieveResponse
from app.services.retrieval_service import RetrievalService
from app.storage.db import get_session
from app.storage.tables import UserRow

router = APIRouter(tags=["retrieval"])


@router.post("/retrieve")
def retrieve(
    request: RetrieveRequest,
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> RetrieveResponse:
    return RetrievalService(session).retrieve(request=request, user=user)
```

## Step 3: Do Not Restore `/query/retrieve` By Default

The current backend intentionally removes `/query/*`. `tests/test_api.py` asserts `/query/retrieve` returns 404.

Do not restore it as part of normal evidence-panel work. If compatibility becomes a new product requirement, add it as a separate API decision and keep it as a thin wrapper around the same service method.

## Step 4: Use One Schema Source of Truth

Current retrieval schemas live in:

```text
app/schemas/retrieval.py
```

Keep `app/schemas/retrieval.py` as the source of truth for evidence-only retrieval. Do not recreate `app/schemas/query.py` for the evidence panel.

## Step 5: Preserve Evidence Response Display Fields

Current `EvidenceResponse` includes explicit display helpers so the WebUI can show source labels without digging through arbitrary metadata.

Current shape:

```python
class EvidenceResponse(BaseModel):
    evidence_id: str
    document_id: str
    source_engine: str
    text: str
    score: float | None = None
    page_start: int | None = None
    page_end: int | None = None
    section_title: str | None = None

    source_path: str | None = None
    document_title: str | None = None
    chunk_id: str | None = None
    reference_id: str | None = None

    metadata: dict = Field(default_factory=dict)
```

`app/retrieval/evidence_mapper.py` projects these fields from evidence metadata:

```python
def to_evidence_response(evidence: Evidence) -> EvidenceResponse:
    metadata = evidence.metadata or {}
    return EvidenceResponse(
        evidence_id=evidence.id,
        document_id=str(evidence.document_id),
        source_engine=evidence.source_engine,
        text=evidence.text,
        score=evidence.score,
        page_start=evidence.page_ref.page_start if evidence.page_ref else None,
        page_end=evidence.page_ref.page_end if evidence.page_ref else None,
        section_title=evidence.section_ref.title if evidence.section_ref else None,
        source_path=metadata.get("source_path"),
        document_title=metadata.get("document_title"),
        chunk_id=metadata.get("chunk_id"),
        reference_id=metadata.get("reference_id"),
        metadata=metadata,
    )
```

This reduces WebUI coupling to metadata internals while preserving raw metadata for debugging. Future work should avoid removing these fields without a contract migration.

## Step 6: Preserve Asset Behavior

The current retrieval request supports:

```text
include_assets
include_thumbnails
max_assets
```

The WebUI should call `/retrieve` with:

```json
{
  "include_assets": true,
  "include_thumbnails": true,
  "max_assets": 5
}
```

The backend should continue to resolve assets using `RetrievalAssetResolver` only when requested.

## Step 7: Validate Domain/Document Filters

Keep the existing validation rule:

```text
If lightrag_domain_id is set and document_ids are set, each selected document must belong to that LightRAG domain.
```

This prevents the WebUI from mixing documents across domains accidentally.

Add or keep tests to make sure `/retrieve` enforces this rule.

## Step 8: Response Behavior

Recommended response behavior:

| Case | Response |
|---|---|
| Evidence found | 200 with `evidence[]` |
| No evidence found | 200 with empty `evidence[]` |
| Invalid domain/document mismatch | 400 |
| Unauthenticated | 401 |
| LightRAG auth error | 502 |
| LightRAG invalid response | 502 |
| LightRAG unavailable | 503 |

Do not convert empty evidence into an error.

## Step 9: Add OpenAPI Tags

Use a clear tag:

```python
APIRouter(tags=["retrieval"])
```

Avoid hiding evidence retrieval under `query` long-term.

## Step 10: Update Docs

Update the project README or API docs with:

```text
POST /retrieve
```

Do not document `/query/retrieve` as supported unless a future API decision restores it.

## Step 11: Run Tests

Run:

```bash
python -m pytest -q
```

Add targeted tests from `docs/04_TEST_PLAN.md`.
