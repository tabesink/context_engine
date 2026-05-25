# Context Engine Review + Retrieve-Only API Simplification Plan



Purpose of this document:

1. Capture the current query/retrieval wiring in the codebase.
2. Identify the API redundancy around `POST /query`, `POST /query/answer`, and `POST /query/retrieve`.
3. Provide a clean implementation plan for a coding agent or junior developer to remove the query/answer API surface and expose a single evidence-only retrieval API:

```text
POST /retrieve
```

---

# 1. Current Codebase Understanding

## 1.1 Current application shape

`context_engine` is currently a backend-only multi-user hybrid RAG service with:

- FastAPI backend
- Authenticated routes
- Admin-only document upload/indexing/admin routes
- PostgreSQL persistence
- Redis/RQ job processing
- Local document navigation retrieval
- Mandatory remote LightRAG for semantic retrieval when enabled
- Terminal UI / CLI client
- LightRAG graph and domain management routes

The repository README states that semantic retrieval is mandatory remote LightRAG and that local navigation retrieval remains available for page/section lookup. The code matches this direction in the routing layer: semantic-like modes route to LightRAG, while navigation routes to the local navigation engine.

---

# 2. Current Retrieval / Query API Surface

## 2.1 Current route file

Current file:

```text
app/api/routes/query.py
```

Current router:

```python
router = APIRouter(prefix="/query", tags=["query"])
```

Current endpoints:

```text
POST /query/retrieve -> RetrievalService.retrieve()
POST /query/answer   -> RetrievalService.answer()
POST /query          -> RetrievalService.answer()
```

Current behavior:

| Endpoint | Current Purpose | Service Method | Response |
|---|---|---|---|
| `POST /query/retrieve` | Evidence-only retrieval | `RetrievalService.retrieve()` | `RetrieveResponse` |
| `POST /query/answer` | Retrieve + composed answer | `RetrievalService.answer()` | `QueryResponse` |
| `POST /query` | Duplicate retrieve + answer endpoint | `RetrievalService.answer()` | `QueryResponse` |

## 2.2 Current request/response schemas

Current file:

```text
app/schemas/query.py
```

Current models:

```text
QueryRequest
EvidenceResponse
AssetResponse
RetrieveResponse
QueryResponse
```

`QueryResponse` extends `RetrieveResponse` by adding:

```python
answer: str
```

This means the application currently treats “query” as a mixed concept:

- Sometimes it means “retrieve evidence”
- Sometimes it means “retrieve evidence and compose an answer”

That is the central API-surface tension.

---

# 3. Current Retrieval Flow

## 3.1 Current high-level flow

```text
Client / TUI
   |
   | POST /query
   | POST /query/answer
   | POST /query/retrieve
   v
app/api/routes/query.py
   |
   v
RetrievalService
   |
   +--> retrieve()
   |      |
   |      +--> _retrieve_and_record()
   |      +--> _retrieve_response()
   |      +--> optional RetrievalAssetResolver
   |
   +--> answer()
          |
          +--> _retrieve_and_record()
          +--> AnswerComposer.compose()
          +--> _retrieve_response()
          +--> QueryResponse
```

## 3.2 Retrieval routing

Current retrieval modes:

```text
auto
semantic
navigation
hybrid
```

Current routing behavior:

| Mode | Backend |
|---|---|
| `auto` | LightRAG |
| `semantic` | LightRAG |
| `hybrid` | LightRAG + optional navigation merge |
| `navigation` | Local navigation |

The important point is that `RetrievalService` already has a clean evidence-only path via:

```python
RetrievalService.retrieve()
```

So the simplify/remove-query work does **not** require redesigning retrieval itself. It mostly requires API-surface cleanup and downstream client/test updates.

---

# 4. Why Remove the Query API

## 4.1 Current problem

There are three query-related endpoints:

```text
POST /query
POST /query/answer
POST /query/retrieve
```

Two of them serve the same answer-oriented purpose:

```text
POST /query
POST /query/answer
```

The third is actually the clean API the backend should expose:

```text
POST /query/retrieve
```

But its path is still nested under `/query`, even though it is evidence retrieval only.

## 4.2 Desired direction

Expose only:

```text
POST /retrieve
```

Remove public answer generation from the backend API.

This makes the backend a cleaner retrieval/context service:

```text
Client
   |
   | POST /retrieve
   v
Context Engine
   |
   +--> authenticated retrieval
   +--> LightRAG semantic retrieval
   +--> local navigation retrieval when requested
   +--> optional asset enrichment
   +--> evidence response
```

Answer composition can be handled later by:

- frontend
- downstream application
- separate LLM orchestration layer
- future dedicated `/answer` service if intentionally needed

Do not keep answer generation as a half-implemented stub in the core backend retrieval API.

---

# 5. Target API Contract

## 5.1 New route

```text
POST /retrieve
```

## 5.2 Auth

Same as current query routes:

```python
user: UserRow = Depends(get_current_user)
session: Session = Depends(get_session)
```

## 5.3 Request body

Recommended target name:

```python
RetrieveRequest
```

Fields:

```python
query: str
mode: RetrievalMode = RetrievalMode.AUTO
document_ids: list[str] | None = None
lightrag_domain_id: str | None = None
top_k: int = Field(default=8, ge=1, le=30)
include_debug: bool = False
include_assets: bool = False
include_thumbnails: bool = True
max_assets: int = Field(default=5, ge=0, le=20)
```

Remove:

```python
allow_general_fallback
```

Reason: `allow_general_fallback` only makes sense for answer generation. A retrieve-only API should not need it.

## 5.4 Response body

Recommended target name:

```python
RetrieveResponse
```

Fields:

```python
query: str
mode: RetrievalMode
evidence: list[EvidenceResponse]
assets: list[AssetResponse] = []
debug: dict | None = None
```

Do not include:

```python
answer
```

---

# 6. Proposed Final Retrieval Architecture

```text
Client / TUI
   |
   | POST /retrieve
   v
app/api/routes/retrieve.py
   |
   v
RetrievalService.retrieve()
   |
   +--> _retrieve_and_record()
   |      |
   |      +--> validate LightRAG document/domain filter
   |      +--> route request
   |      +--> execute selected retrieval strategy
   |      +--> record query/retrieval log
   |
   +--> _retrieve_response()
          |
          +--> evidence mapping
          +--> optional asset resolver
          +--> admin-only debug
          v
RetrieveResponse
```

---

# 7. Implementation Plan

## Phase 1 — Add the new retrieve-only route

Create a new route file:

```text
app/api/routes/retrieve.py
```

Suggested implementation:

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

Then update:

```text
app/main.py
```

Replace:

```python
from app.api.routes import admin, auth, documents, health, jobs, lightrag, lightrag_admin, query
```

With:

```python
from app.api.routes import admin, auth, documents, health, jobs, lightrag, lightrag_admin, retrieve
```

Replace:

```python
app.include_router(query.router)
```

With:

```python
app.include_router(retrieve.router)
```

Acceptance check:

```text
POST /retrieve works
POST /query/retrieve still works only if old query router remains temporarily
```

For the final clean state, the old query router should be removed.

---

## Phase 2 — Rename schema from query to retrieval

Current file:

```text
app/schemas/query.py
```

Recommended target:

```text
app/schemas/retrieval.py
```

Recommended changes:

1. Rename `QueryRequest` to `RetrieveRequest`.
2. Keep `EvidenceResponse`.
3. Keep `AssetResponse`.
4. Keep `RetrieveResponse`.
5. Delete `QueryResponse`.
6. Delete `allow_general_fallback`.

Target file shape:

```python
from pydantic import BaseModel, Field

from app.domain.models import RetrievalMode


class RetrieveRequest(BaseModel):
    query: str = Field(min_length=1)
    mode: RetrievalMode = RetrievalMode.AUTO
    document_ids: list[str] | None = None
    lightrag_domain_id: str | None = None
    top_k: int = Field(default=8, ge=1, le=30)
    include_debug: bool = False
    include_assets: bool = False
    include_thumbnails: bool = True
    max_assets: int = Field(default=5, ge=0, le=20)


class EvidenceResponse(BaseModel):
    evidence_id: str
    document_id: str
    source_engine: str
    text: str
    score: float | None = None
    page_start: int | None = None
    page_end: int | None = None
    section_title: str | None = None
    metadata: dict = {}


class AssetResponse(BaseModel):
    asset_id: str
    document_id: str
    asset_type: str
    caption: str | None = None
    page_number: int | None = None
    url: str
    thumbnail_url: str | None = None


class RetrieveResponse(BaseModel):
    query: str
    mode: RetrievalMode
    evidence: list[EvidenceResponse]
    assets: list[AssetResponse] = []
    debug: dict | None = None
```

Then update imports across the codebase:

```bash
rg "app.schemas.query|QueryRequest|QueryResponse|allow_general_fallback"
```

Expected updates:

```text
app/api/routes/retrieve.py
app/services/retrieval_service.py
app/retrieval/evidence_mapper.py
app/services/retrieval_asset_resolver.py
tests/*
cli/*
```

---

## Phase 3 — Remove answer-generation path from RetrievalService

Current file:

```text
app/services/retrieval_service.py
```

Remove imports:

```python
from app.retrieval.answer_composer import AnswerComposer
from app.schemas.query import QueryResponse
```

Remove constructor dependency:

```python
answer_composer: AnswerComposer | None = None
```

Remove initialization:

```python
self.answer_composer = answer_composer or AnswerComposer()
```

Delete method:

```python
def answer(...)
```

Update type imports to use retrieval schema:

```python
from app.schemas.retrieval import RetrieveRequest, RetrieveResponse
```

Update method signatures:

```python
def retrieve(self, *, request: RetrieveRequest, user: UserRow) -> RetrieveResponse:
    ...
```

```python
def _retrieve_and_record(self, *, request: RetrieveRequest, user: UserRow) -> RetrievalResult:
    ...
```

```python
def _retrieve_result(self, *, request: RetrieveRequest, user: UserRow) -> RetrievalResult:
    ...
```

```python
def _validate_lightrag_document_filter(self, request: RetrieveRequest) -> None:
    ...
```

```python
def _retrieve_response(
    self,
    result: RetrievalResult,
    *,
    request: RetrieveRequest,
    include_debug: bool,
) -> RetrieveResponse:
    ...
```

Acceptance check:

```bash
rg "AnswerComposer|QueryResponse|allow_general_fallback|def answer"
```

Expected result after cleanup:

```text
No matches in app/
```

---

## Phase 4 — Delete the old query route

Delete:

```text
app/api/routes/query.py
```

Ensure `app/main.py` no longer imports or includes it.

Acceptance checks:

```bash
rg "include_router\(query|routes import .*query|APIRouter\(prefix=\"/query\""
```

Expected result:

```text
No matches
```

API behavior:

| Endpoint | Expected Final Result |
|---|---|
| `POST /retrieve` | `200` with `RetrieveResponse` |
| `POST /query/retrieve` | `404` |
| `POST /query/answer` | `404` |
| `POST /query` | `404` |

---

## Phase 5 — Delete answer composer if no longer used

Current file:

```text
app/retrieval/answer_composer.py
```

Delete this file if no other code uses it.

Delete or rewrite test:

```text
tests/test_answer_composer.py
```

Acceptance check:

```bash
rg "answer_composer|AnswerComposer"
```

Expected result:

```text
No matches
```

---

## Phase 6 — Update CLI/TUI retrieval service

Current file:

```text
cli/services/retrieval.py
```

Current behavior:

```python
self._client.post("/query/retrieve", payload)
self._client.post("/query/answer", payload)
```

Target behavior:

```python
self._client.post("/retrieve", payload)
```

Remove:

```python
def answer(...)
```

Recommended target:

```python
"""Retrieval route wrappers."""
from __future__ import annotations

from typing import Any, Literal

from cli.api_client import ApiClient
from cli.retrieve_payload import build_retrieve_payload

RetrievalMode = Literal["auto", "semantic", "navigation", "hybrid"]


class RetrievalService:
    def __init__(self, client: ApiClient):
        self._client = client

    def retrieve(
        self,
        *,
        query: str,
        mode: RetrievalMode,
        top_k: int,
        include_debug: bool = False,
        lightrag_domain_id: str | None = None,
        document_ids: list[str] | None = None,
        include_assets: bool = False,
    ) -> dict[str, Any]:
        payload = build_retrieve_payload(
            query=query,
            mode=mode,
            top_k=top_k,
            include_debug=include_debug,
            lightrag_domain_id=lightrag_domain_id,
            document_ids=document_ids,
            include_assets=include_assets,
        )
        response = self._client.post("/retrieve", payload)
        return response if isinstance(response, dict) else {}
```

---

## Phase 7 — Rename CLI query payload builder

Current file:

```text
cli/query_payload.py
```

Recommended target:

```text
cli/retrieve_payload.py
```

Current issue discovered during review:

The test expects `lightrag_domain_id`, but the current payload builder shown in the repo does not accept `lightrag_domain_id`. This should be fixed as part of the retrieve-only cleanup.

Recommended target implementation:

```python
from typing import Any

from app.schemas.retrieval import RetrieveRequest


def build_retrieve_payload(
    *,
    query: str,
    mode: str,
    top_k: int,
    include_debug: bool,
    document_ids: list[str] | None = None,
    lightrag_domain_id: str | None = None,
    include_assets: bool = False,
    include_thumbnails: bool = True,
    max_assets: int = 5,
) -> dict[str, Any]:
    request = RetrieveRequest(
        query=query,
        mode=mode,
        top_k=top_k,
        include_debug=include_debug,
        document_ids=document_ids,
        lightrag_domain_id=lightrag_domain_id,
        include_assets=include_assets,
        include_thumbnails=include_thumbnails,
        max_assets=max_assets,
    )

    payload = request.model_dump(mode="json")

    if payload.get("document_ids") is None:
        payload.pop("document_ids")

    if payload.get("lightrag_domain_id") is None:
        payload.pop("lightrag_domain_id")

    return payload
```

Then update imports:

```bash
rg "query_payload|build_query_payload"
```

Replace with:

```text
retrieve_payload
build_retrieve_payload
```

---

## Phase 8 — Update CLI/TUI screens

Current file:

```text
cli/screens/retrieval.py
```

Current answer-related items to remove or simplify:

```python
build_answer_screen(...)
ScreenAction("Ask with answer", ...)
ScreenAction("Retrieve only", ...)
```

Recommended final state:

- Keep one retrieval screen builder.
- Remove answer screen builder if unused.
- Remove “Ask with answer” action.
- Rename user-facing labels from “query” to “retrieve” where appropriate.

Recommended action labels:

```text
Retrieve semantic
Retrieve hybrid
Retrieve navigation
```

Avoid user-facing labels like:

```text
Ask with answer
Query
Answer
```

unless those features are intentionally reintroduced later.

---

## Phase 9 — Update tests

Update or delete tests according to the new retrieve-only API.

## 9.1 Add route test

Add/modify an API test confirming:

```text
POST /retrieve returns evidence-only response
```

Expected assertions:

```python
assert response.status_code == 200
payload = response.json()
assert "evidence" in payload
assert "answer" not in payload
```

## 9.2 Add removed route tests

Add tests confirming old query routes are gone:

```python
assert client.post("/query", json=payload, headers=headers).status_code == 404
assert client.post("/query/answer", json=payload, headers=headers).status_code == 404
assert client.post("/query/retrieve", json=payload, headers=headers).status_code == 404
```

## 9.3 Update CLI tests

Rename:

```text
tests/test_cli_query_payload.py
```

To:

```text
tests/test_cli_retrieve_payload.py
```

Update expectations:

```python
from cli.retrieve_payload import build_retrieve_payload
```

Remove:

```text
allow_general_fallback
```

Keep or add:

```text
lightrag_domain_id
include_assets
```

## 9.4 Delete answer composer tests

Delete:

```text
tests/test_answer_composer.py
```

Only keep if `AnswerComposer` remains intentionally used somewhere else.

---

## Phase 10 — Update documentation

Update all docs and prompts that mention:

```text
/query
/query/answer
/query/retrieve
QueryResponse
QueryRequest
AnswerComposer
allow_general_fallback
```

Use:

```text
/retrieve
RetrieveRequest
RetrieveResponse
```

Search command:

```bash
rg "/query|query/answer|query/retrieve|QueryResponse|QueryRequest|AnswerComposer|allow_general_fallback"
```

Suggested docs to check:

```text
README.md
CONTEXT.md
docs/
.prompts/
.references/
cli screen examples
```

---

# 8. Optional Database Naming Cleanup

Current code logs retrieval requests into:

```text
query_logs
```

Recommendation for this task:

Do **not** rename the database table in this pass.

Reason:

- Renaming `query_logs` to `retrieval_logs` requires a migration.
- It adds risk without improving the public API surface.
- The table can be cleaned later as a separate DB naming migration.

For now, keep:

```text
query_logs
```

But consider changing code-level wording later:

```text
record_query(...)
```

to:

```text
record_retrieval(...)
```

as a follow-up cleanup.

---

# 9. Final Target Route Table

| Method | Path | Auth | Role | Request | Response | Purpose |
|---|---|---|---|---|---|---|
| `POST` | `/retrieve` | Yes | User/Admin | `RetrieveRequest` | `RetrieveResponse` | Retrieve evidence/context only |

Removed routes:

| Method | Path | Final Status |
|---|---|---|
| `POST` | `/query` | Removed |
| `POST` | `/query/answer` | Removed |
| `POST` | `/query/retrieve` | Removed |

---

# 10. Acceptance Criteria

## API

- [ ] `POST /retrieve` exists.
- [ ] `POST /retrieve` requires authentication.
- [ ] `POST /retrieve` returns `RetrieveResponse`.
- [ ] `POST /retrieve` does not return `answer`.
- [ ] `POST /query` returns `404`.
- [ ] `POST /query/answer` returns `404`.
- [ ] `POST /query/retrieve` returns `404`.
- [ ] OpenAPI schema contains `/retrieve`.
- [ ] OpenAPI schema does not contain `/query`, `/query/answer`, or `/query/retrieve`.

## Service layer

- [ ] `RetrievalService.retrieve()` remains.
- [ ] `RetrievalService.answer()` is removed.
- [ ] `AnswerComposer` is removed if unused.
- [ ] `QueryResponse` is removed.
- [ ] `allow_general_fallback` is removed.
- [ ] Asset enrichment still works through `include_assets`.
- [ ] Admin-only debug behavior still works.

## CLI/TUI

- [ ] CLI retrieval service posts to `/retrieve`.
- [ ] CLI no longer calls `/query/retrieve`.
- [ ] CLI no longer calls `/query/answer`.
- [ ] Retrieval screen does not show “Ask with answer”.
- [ ] Query payload builder is renamed or cleaned to retrieve payload builder.
- [ ] `lightrag_domain_id` is supported by the payload builder.

## Tests

- [ ] Retrieval route tests pass.
- [ ] Old query route removal tests pass.
- [ ] CLI retrieve payload tests pass.
- [ ] Retrieval asset enrichment tests pass.
- [ ] Retrieval routing policy tests pass.
- [ ] No tests reference `QueryResponse`, `AnswerComposer`, or `/query`.

Run:

```bash
python -m pytest -q
```

Run static search checks:

```bash
rg "/query|query/answer|query/retrieve|QueryResponse|AnswerComposer|allow_general_fallback"
```

Expected result:

```text
Only historical documentation references, if intentionally kept.
No live app, CLI, or test references.
```

---

# 11. Coding Agent Prompt

Use the following prompt with a coding agent.

```markdown
# Task: Simplify Context Engine Retrieval API to One Retrieve-Only Endpoint

You are working in:

https://github.com/tabesink/context_engine.git

Goal:

Remove the query/answer API surface and expose one evidence-only retrieval endpoint:

POST /retrieve

Current redundant endpoints:

- POST /query
- POST /query/answer
- POST /query/retrieve

Desired final state:

- Keep only POST /retrieve.
- Remove public answer-generation behavior.
- Remove RetrievalService.answer().
- Remove QueryResponse.
- Remove allow_general_fallback.
- Remove AnswerComposer if unused.
- Update CLI/TUI to call /retrieve only.
- Update tests and docs.

Important architectural constraint:

The backend should be a retrieval/context service. It should return evidence, source metadata, optional assets, and admin debug details. It should not compose natural-language answers in this pass.

Required implementation steps:

1. Create app/api/routes/retrieve.py with POST /retrieve.
2. Update app/main.py to include retrieve.router and remove query.router.
3. Delete app/api/routes/query.py.
4. Rename or replace app/schemas/query.py with app/schemas/retrieval.py.
5. Rename QueryRequest to RetrieveRequest.
6. Keep EvidenceResponse, AssetResponse, RetrieveResponse.
7. Delete QueryResponse.
8. Remove allow_general_fallback from request schema.
9. Update RetrievalService to expose retrieve() only.
10. Remove RetrievalService.answer().
11. Remove AnswerComposer and its tests if no longer used.
12. Update cli/services/retrieval.py to call /retrieve.
13. Rename cli/query_payload.py to cli/retrieve_payload.py or otherwise clean naming.
14. Ensure the CLI payload builder supports lightrag_domain_id.
15. Remove answer-related TUI actions/screens.
16. Update tests:
    - POST /retrieve works.
    - POST /query, /query/answer, /query/retrieve return 404.
    - response has evidence but no answer.
    - CLI uses /retrieve.
17. Update README/docs/prompts/examples to reference /retrieve only.

Do not change:

- LightRAG retrieval routing behavior.
- Navigation retrieval behavior.
- Document upload/indexing behavior.
- LightRAG domain deployment behavior.
- Database table names in this pass.

Acceptance checks:

python -m pytest -q

rg "/query|query/answer|query/retrieve|QueryResponse|AnswerComposer|allow_general_fallback"

No live app/CLI/test references to removed query/answer API should remain.
```

---

# 12. Recommended Follow-Up After This Cleanup

After this retrieve-only refactor, do a second focused pass on naming and persistence:

1. Decide whether `query_logs` should become `retrieval_logs`.
2. Decide whether `LogRepository.record_query()` should become `record_retrieval()`.
3. Confirm whether `QueryRequest` naming exists anywhere after schema cleanup.
4. Decide whether frontend/client docs should describe this service as a “retrieval API” instead of a “query API”.
5. Add an API contract document for `/retrieve`.

Do not combine this with the first cleanup unless the codebase is already stable and tests are passing.
