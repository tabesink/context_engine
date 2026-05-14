# Development Plan: Multi-User Hybrid RAG Application

## 0. Project Goal

Build a multi-user RAG application for 5–10 users that combines:

1. **LightRAG-style semantic retrieval**

   * chunk-level retrieval
   * vector retrieval
   * graph/entity/relation retrieval
   * hybrid semantic search across documents

2. **PageIndex-style document navigation**

   * document tree / table-of-contents indexing
   * section-aware retrieval
   * page-range retrieval
   * explainable document navigation

3. **FastAPI server**

   * concurrent read/query operations for normal users
   * admin-only write/index/delete operations
   * clean API boundaries
   * easy-to-understand codebase structure

The objective is **not** to build toy/simple RAG code. The objective is to build a capable RAG system with senior-level architecture that a junior developer can understand by reading the folder structure, names, docs, tests, and request flow.

---

## 1. Design Principle

Use this principle everywhere:

> Merge capabilities, not internal complexity.

LightRAG and PageIndex should not be mashed into one giant class. Instead, build a shared application layer around two retrieval engines:

```text
User query
  ↓
FastAPI route
  ↓
Retrieval service
  ↓
Retrieval router
  ↓
Semantic engine      Document navigation engine
LightRAG-style       PageIndex-style
  ↓                  ↓
Evidence objects     Evidence objects
  ↓
Answer composer
  ↓
API response with citations
```

The unified system should have:

* one API
* one user/permission model
* one document registry
* one job system
* one evidence/citation model
* one answer-composition pipeline
* two specialized retrieval engines

---

## 2. Target Users and Permissions

### Roles

| Role    | Capabilities                                                                                             |
| ------- | -------------------------------------------------------------------------------------------------------- |
| `admin` | Upload documents, index documents, delete documents, rebuild indexes, view jobs, view logs, manage users |
| `user`  | Query indexed documents, inspect citations, view allowed documents                                       |

### Rule

Normal users should never directly mutate the RAG index.

All write operations must be admin-only:

* upload document
* index document
* re-index document
* delete document
* delete index
* modify collection/workspace metadata
* trigger LightRAG graph rebuild
* trigger PageIndex tree rebuild

Read operations may be available to all authenticated users:

* query
* retrieve evidence
* inspect document metadata
* get document structure
* get page content
* get conversation history, if enabled

---

## 3. Core Capabilities

### 3.1 Semantic Retrieval Capabilities

The semantic engine should provide:

* vector similarity retrieval
* chunk retrieval
* entity retrieval
* relationship retrieval
* graph-aware retrieval
* optional reranking
* cross-document synthesis

This engine should be used for questions like:

```text
What are the common warranty terms across these manuals?
Which suppliers are associated with specific products?
What are the recurring failure modes mentioned across documents?
Summarize all documents related to alternating pressure mattresses.
```

### 3.2 Document Navigation Capabilities

The document-navigation engine should provide:

* document tree generation
* section summaries
* page-range lookup
* page content lookup
* section-level retrieval
* transparent citations by page and section

This engine should be used for questions like:

```text
Where in this manual does it explain pendant reset behavior?
Show me the section that describes pump alarms.
What does page 17 say about installation?
Find the exact page range discussing maintenance.
```

### 3.3 Hybrid Retrieval Capabilities

The hybrid system should support these query modes:

| Mode         | Meaning                                                          |
| ------------ | ---------------------------------------------------------------- |
| `semantic`   | Use only the LightRAG-style semantic engine                      |
| `navigation` | Use only the PageIndex-style document-navigation engine          |
| `hybrid`     | Query both engines, merge evidence, answer from combined context |
| `auto`       | Router chooses one or both engines based on query intent         |

Default mode should be `auto`.

---

## 4. System Architecture

```text
app/
  main.py
  core/
    config.py
    logging.py
    security.py
    errors.py

  api/
    deps.py
    routes/
      auth.py
      users.py
      documents.py
      query.py
      admin.py
      jobs.py
      health.py

  domain/
    models.py
    permissions.py
    events.py

  services/
    document_service.py
    ingestion_service.py
    indexing_service.py
    retrieval_service.py
    answer_service.py
    job_service.py
    audit_service.py

  retrieval/
    base.py
    router.py
    evidence.py
    semantic_engine.py
    navigation_engine.py
    hybrid_merger.py
    answer_composer.py

  indexing/
    parsers.py
    chunking.py
    page_tree_builder.py
    semantic_index_builder.py
    navigation_index_builder.py

  storage/
    db.py
    repositories/
      users.py
      documents.py
      jobs.py
      audit_logs.py
      conversations.py
    object_store.py
    index_store.py

  integrations/
    lightrag_adapter.py
    pageindex_adapter.py
    llm_provider.py
    embedding_provider.py

  workers/
    tasks.py
    queue.py
    locks.py

  schemas/
    auth.py
    documents.py
    query.py
    jobs.py
    common.py

tests/
  unit/
  integration/
  e2e/

docs/
  architecture.md
  api.md
  retrieval_flow.md
  indexing_flow.md
  permissions.md
  junior_dev_start_here.md
```

---

## 5. Module Ownership Rules

These rules are important for keeping the codebase understandable.

### API layer owns HTTP only

Files in `api/routes/` should:

* parse request schemas
* call services
* return response schemas
* enforce route-level permissions through dependencies

They should not:

* know LightRAG internals
* know PageIndex internals
* build prompts
* access vector stores directly
* access graph stores directly

### Services own application use cases

Files in `services/` should coordinate workflows.

Example:

```text
UploadDocumentUseCase
  → validate user permission
  → save file
  → create document record
  → enqueue indexing job
```

Services should not contain low-level graph/vector/tree logic.

### Retrieval engines own retrieval details

Files in `retrieval/` should expose consistent retrieval interfaces.

The rest of the app should not care whether evidence came from LightRAG, PageIndex, vector search, graph search, or page-tree search.

### Integrations isolate third-party libraries

Files in `integrations/` should wrap external libraries.

If LightRAG or PageIndex changes its API, most changes should stay inside:

```text
integrations/lightrag_adapter.py
integrations/pageindex_adapter.py
```

---

## 6. Core Domain Models

Create these first. They are the vocabulary of the whole system.

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class UserRole(StrEnum):
    ADMIN = "admin"
    USER = "user"


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"


class RetrievalMode(StrEnum):
    AUTO = "auto"
    SEMANTIC = "semantic"
    NAVIGATION = "navigation"
    HYBRID = "hybrid"


@dataclass
class User:
    id: UUID
    email: str
    role: UserRole
    is_active: bool = True


@dataclass
class Document:
    id: UUID
    owner_id: UUID | None
    filename: str
    content_type: str
    storage_path: str
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PageRef:
    document_id: UUID
    page_start: int | None = None
    page_end: int | None = None


@dataclass
class SectionRef:
    document_id: UUID
    section_id: str
    title: str
    page_start: int | None = None
    page_end: int | None = None


@dataclass
class Evidence:
    id: str
    document_id: UUID
    source_engine: str
    text: str
    score: float | None = None
    page_ref: PageRef | None = None
    section_ref: SectionRef | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalResult:
    query: str
    mode: RetrievalMode
    evidence: list[Evidence]
    debug: dict[str, Any] = field(default_factory=dict)
```

---

## 7. Retrieval Interfaces

Use one retrieval protocol for both engines.

```python
from typing import Protocol
from uuid import UUID


class RetrievalEngine(Protocol):
    name: str

    async def retrieve(
        self,
        *,
        query: str,
        document_ids: list[UUID] | None,
        top_k: int,
        user_id: UUID,
    ) -> list[Evidence]:
        ...
```

### Semantic engine

```python
class SemanticRetrievalEngine:
    name = "semantic"

    def __init__(self, lightrag_adapter: LightRAGAdapter):
        self.lightrag_adapter = lightrag_adapter

    async def retrieve(self, *, query, document_ids, top_k, user_id):
        raw_results = await self.lightrag_adapter.query(
            query=query,
            document_ids=document_ids,
            top_k=top_k,
        )
        return self.lightrag_adapter.to_evidence(raw_results)
```

### Navigation engine

```python
class NavigationRetrievalEngine:
    name = "navigation"

    def __init__(self, pageindex_adapter: PageIndexAdapter):
        self.pageindex_adapter = pageindex_adapter

    async def retrieve(self, *, query, document_ids, top_k, user_id):
        raw_results = await self.pageindex_adapter.retrieve_sections(
            query=query,
            document_ids=document_ids,
            top_k=top_k,
        )
        return self.pageindex_adapter.to_evidence(raw_results)
```

### Router

```python
class RetrievalRouter:
    def __init__(
        self,
        semantic_engine: RetrievalEngine,
        navigation_engine: RetrievalEngine,
    ):
        self.semantic_engine = semantic_engine
        self.navigation_engine = navigation_engine

    async def retrieve(
        self,
        *,
        query: str,
        mode: RetrievalMode,
        document_ids: list[UUID] | None,
        top_k: int,
        user_id: UUID,
    ) -> RetrievalResult:
        if mode == RetrievalMode.SEMANTIC:
            evidence = await self.semantic_engine.retrieve(
                query=query,
                document_ids=document_ids,
                top_k=top_k,
                user_id=user_id,
            )
            return RetrievalResult(query=query, mode=mode, evidence=evidence)

        if mode == RetrievalMode.NAVIGATION:
            evidence = await self.navigation_engine.retrieve(
                query=query,
                document_ids=document_ids,
                top_k=top_k,
                user_id=user_id,
            )
            return RetrievalResult(query=query, mode=mode, evidence=evidence)

        if mode == RetrievalMode.HYBRID:
            semantic, navigation = await gather_both_engines(
                self.semantic_engine,
                self.navigation_engine,
                query=query,
                document_ids=document_ids,
                top_k=top_k,
                user_id=user_id,
            )
            evidence = merge_evidence(semantic + navigation, top_k=top_k)
            return RetrievalResult(query=query, mode=mode, evidence=evidence)

        selected_mode = classify_query_intent(query)
        return await self.retrieve(
            query=query,
            mode=selected_mode,
            document_ids=document_ids,
            top_k=top_k,
            user_id=user_id,
        )
```

---

## 8. Query Intent Routing

Start with simple deterministic routing before adding LLM routing.

### Rule-based routing v1

Use `navigation` when the query contains:

```text
page, section, chapter, where, show me, exact, manual, table, installation, instructions, step, maintenance, appendix
```

Use `semantic` when the query contains:

```text
compare, summarize across, relationship, related to, common themes, entities, suppliers, products, policies, similar, all documents
```

Use `hybrid` when:

* the query is broad but asks for source-specific evidence
* the query references multiple documents and also asks for exact sections/pages
* confidence is low

### LLM router v2

Later add an LLM-based router that outputs:

```json
{
  "mode": "semantic | navigation | hybrid",
  "reason": "...",
  "needs_page_level_evidence": true,
  "needs_cross_document_reasoning": false
}
```

Keep the LLM router optional. The deterministic router should always exist as fallback.

---

## 9. API Design

### Authentication

```text
POST /auth/login
POST /auth/refresh
GET  /auth/me
```

### Documents

Read endpoints available to authenticated users:

```text
GET /documents
GET /documents/{document_id}
GET /documents/{document_id}/structure
GET /documents/{document_id}/pages/{page_number}
```

Admin-only write endpoints:

```text
POST   /admin/documents/upload
POST   /admin/documents/{document_id}/index
POST   /admin/documents/{document_id}/reindex
DELETE /admin/documents/{document_id}
POST   /admin/index/rebuild
```

### Query endpoints

```text
POST /query
POST /query/retrieve
POST /query/answer
```

Recommended separation:

| Endpoint          | Purpose                             |
| ----------------- | ----------------------------------- |
| `/query/retrieve` | returns evidence only               |
| `/query/answer`   | returns answer and citations        |
| `/query`          | convenience endpoint that does both |

### Jobs

```text
GET /jobs
GET /jobs/{job_id}
POST /jobs/{job_id}/cancel
```

Admin can see all jobs. Normal users can see only their own query jobs if query jobs are persisted.

### Health

```text
GET /health
GET /health/readiness
GET /health/index-status
```

---

## 10. Example Request/Response Schemas

### Query request

```python
from pydantic import BaseModel, Field
from uuid import UUID


class QueryRequest(BaseModel):
    query: str = Field(min_length=1)
    mode: RetrievalMode = RetrievalMode.AUTO
    document_ids: list[UUID] | None = None
    top_k: int = Field(default=8, ge=1, le=30)
    include_debug: bool = False
```

### Query response

```python
class EvidenceResponse(BaseModel):
    evidence_id: str
    document_id: UUID
    source_engine: str
    text: str
    score: float | None = None
    page_start: int | None = None
    page_end: int | None = None
    section_title: str | None = None
    metadata: dict = {}


class QueryResponse(BaseModel):
    query: str
    mode: RetrievalMode
    answer: str
    evidence: list[EvidenceResponse]
    debug: dict | None = None
```

---

## 11. Storage Strategy

For a 5–10 user application, do not start with too many storage systems.

### Recommended v1

| Data                                              | Storage                                                         |
| ------------------------------------------------- | --------------------------------------------------------------- |
| users, roles, document registry, jobs, audit logs | PostgreSQL                                                      |
| uploaded files                                    | local filesystem or S3-compatible object storage                |
| extracted text/pages                              | filesystem JSON or PostgreSQL JSONB                             |
| PageIndex tree                                    | filesystem JSON or PostgreSQL JSONB                             |
| vector embeddings                                 | pgvector or LightRAG configured vector backend                  |
| graph data                                        | LightRAG default graph storage first, then Neo4j only if needed |
| conversations                                     | PostgreSQL                                                      |

### Why this is enough

For 5–10 users, the risk is not scale. The risk is architectural confusion.

Start with one relational database and one file/object store. Add specialized stores only when a clear bottleneck appears.

---

## 12. Indexing Flow

Admin upload should not block the HTTP request until indexing finishes.

```text
Admin uploads PDF
  ↓
API stores file
  ↓
Document row created with status=uploaded
  ↓
Indexing job created
  ↓
Worker parses document
  ↓
Worker builds page model
  ↓
Worker builds PageIndex tree
  ↓
Worker builds LightRAG semantic index
  ↓
Document status=ready
```

### Indexing phases per document

```text
uploaded
parsing
building_navigation_index
building_semantic_index
ready
failed
```

Store each phase in the job table so admins can debug failures.

---

## 13. Write Concurrency Rules

Because only admins can write, keep write concurrency simple.

### Rules

1. Only one active indexing job per document.
2. Users can query only documents with `status=ready`.
3. Reindexing creates a new index version.
4. Existing ready index remains active until the new index version succeeds.
5. Deleting a document marks it as deleted first, then asynchronously removes files/indexes.

### Index versioning

Use this model:

```text
document_id
index_version
semantic_index_status
navigation_index_status
is_active
created_at
```

This prevents users from hitting half-built indexes.

---

## 14. Worker Strategy

### MVP option

Use FastAPI `BackgroundTasks` for simple local development.

### Production-preferred option

Use a real job queue:

* Redis + RQ
* Redis + ARQ
* Celery + Redis
* Dramatiq + Redis

Recommended for this project:

```text
Redis + RQ or ARQ
```

Keep queue logic isolated in:

```text
workers/queue.py
workers/tasks.py
workers/locks.py
```

FastAPI should enqueue jobs. Workers should run indexing.

---

## 15. Answer Generation Flow

```text
QueryRequest
  ↓
validate user/document access
  ↓
retrieve evidence
  ↓
deduplicate/merge evidence
  ↓
compose answer prompt
  ↓
call LLM
  ↓
return answer + citations
```

The answer composer must never invent citations. It can only cite returned `Evidence` objects.

### Answer composer rules

1. Use only retrieved evidence.
2. Mention uncertainty when evidence is weak.
3. Return page/section citations when available.
4. Prefer PageIndex evidence for exact manual/document-location questions.
5. Prefer LightRAG evidence for cross-document synthesis.
6. If engines disagree, show both sources and state the conflict.

---

## 16. Admin Dashboard Requirements

Admin should be able to see:

* uploaded documents
* document status
* indexing jobs
* failed jobs
* error messages
* index versions
* query volume
* average retrieval latency
* LLM cost estimate
* top documents queried
* slow queries

Admin should be able to trigger:

* upload
* reindex
* delete
* rebuild all indexes
* retry failed job

---

## 17. Observability and Debugging

Add structured logging from day one.

Every query should log:

```json
{
  "event": "query.completed",
  "user_id": "...",
  "query_id": "...",
  "mode": "hybrid",
  "selected_engines": ["semantic", "navigation"],
  "document_ids": ["..."],
  "evidence_count": 8,
  "latency_ms": 1320,
  "llm_model": "...",
  "estimated_cost_usd": 0.0032
}
```

Every indexing job should log:

```json
{
  "event": "indexing.completed",
  "document_id": "...",
  "job_id": "...",
  "pages": 120,
  "navigation_nodes": 85,
  "semantic_chunks": 430,
  "latency_ms": 80422
}
```

### Minimum metrics

Track:

* query latency
* semantic retrieval latency
* navigation retrieval latency
* LLM answer latency
* indexing latency
* indexing failures
* token usage
* estimated cost
* number of documents indexed
* number of queries per user

---

## 18. Security and Access Control

### Auth

Use JWT access tokens with role claims.

Example claims:

```json
{
  "sub": "user-id",
  "email": "user@example.com",
  "role": "admin"
}
```

### Permissions

Implement dependencies:

```python
async def get_current_user() -> User:
    ...

async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
```

Use `require_admin` on all write routes.

### Document access

For v1, all authenticated users may query all ready documents.

For v2, add document-level ACLs:

```text
document_permissions
  document_id
  user_id
  permission: read | write | admin
```

---

## 19. Development Phases

# Phase 0 — Repository Setup and Architecture Skeleton

## Goal

Create the project structure, configuration, and documentation before adding RAG complexity.

## Tasks

1. Create FastAPI project structure.
2. Add `pyproject.toml` or `requirements.txt`.
3. Add `.env.example`.
4. Add `docs/architecture.md`.
5. Add `docs/junior_dev_start_here.md`.
6. Add health endpoint.
7. Add structured logging.
8. Add basic test setup.

## Acceptance Criteria

* `GET /health` returns OK.
* Tests run with one command.
* Project folder structure matches the architecture.
* Junior dev can read `docs/junior_dev_start_here.md` and understand where API, services, retrieval, indexing, and storage live.

---

# Phase 1 — Auth, Users, Roles, and Admin-Only Write Guardrails

## Goal

Build the security foundation before indexing documents.

## Tasks

1. Add `User`, `UserRole` models.
2. Add login endpoint.
3. Add JWT auth.
4. Add `get_current_user` dependency.
5. Add `require_admin` dependency.
6. Add seed admin script.
7. Add tests proving users cannot access admin endpoints.

## Acceptance Criteria

* Admin can access `/admin/*`.
* Normal user receives 403 on `/admin/*`.
* Authenticated users can access read/query endpoints.
* Tests cover role enforcement.

---

# Phase 2 — Document Registry and File Upload

## Goal

Allow admins to upload documents and store metadata safely.

## Tasks

1. Add document DB table.
2. Add object/file storage abstraction.
3. Add admin upload endpoint.
4. Add document listing endpoint.
5. Add document detail endpoint.
6. Add document status lifecycle.
7. Add audit log for uploads.

## Acceptance Criteria

* Admin can upload PDF/Markdown/text documents.
* User can list ready documents.
* Uploaded documents start as `uploaded` or `indexing`.
* File path and metadata are stored.
* Normal users cannot upload.

---

# Phase 3 — Normalized Document Parsing Layer

## Goal

Parse documents once and provide normalized outputs to both retrieval engines.

## Tasks

1. Add `Document`, `Page`, `ParsedDocument` models.
2. Implement PDF parser.
3. Implement Markdown parser.
4. Store extracted page text.
5. Add parser smoke tests.

## Normalized Output

```python
@dataclass
class ParsedDocument:
    document_id: UUID
    title: str
    pages: list[Page]
    full_text: str
    metadata: dict
```

## Acceptance Criteria

* Given a PDF, parser produces pages.
* Given Markdown, parser produces pseudo-pages or sections.
* Parsing output can be saved and loaded.
* No retrieval engine directly parses raw files.

---

# Phase 4 — PageIndex-Style Navigation Index

## Goal

Add document tree/page-navigation capability.

## Tasks

1. Add `SectionNode` model.
2. Add `NavigationIndexBuilder`.
3. Wrap PageIndex logic in `PageIndexAdapter`.
4. Build tree structure from parsed document.
5. Store tree JSON.
6. Add `GET /documents/{id}/structure`.
7. Add `GET /documents/{id}/pages/{page}`.
8. Add `NavigationRetrievalEngine`.
9. Add retrieval tests.

## Acceptance Criteria

* Admin can build navigation index for a document.
* User can inspect document structure.
* User can retrieve page content.
* Querying navigation engine returns `Evidence` with page and section references.

---

# Phase 5 — LightRAG-Style Semantic Index

## Goal

Add semantic/vector/graph retrieval.

## Tasks

1. Add `LightRAGAdapter`.
2. Add semantic index builder.
3. Add chunking strategy.
4. Insert parsed document text/chunks into LightRAG-style index.
5. Add `SemanticRetrievalEngine`.
6. Convert LightRAG results into common `Evidence` objects.
7. Add semantic retrieval tests.

## Acceptance Criteria

* Admin can build semantic index for a document.
* Semantic retrieval returns relevant chunk/entity/graph evidence.
* Returned evidence uses the same `Evidence` model as navigation retrieval.
* Query endpoint can run semantic-only mode.

---

# Phase 6 — Hybrid Retrieval Router

## Goal

Expose semantic, navigation, hybrid, and auto retrieval modes through one API.

## Tasks

1. Add `RetrievalMode` enum.
2. Add `RetrievalRouter`.
3. Add deterministic query classifier.
4. Add hybrid evidence merger.
5. Add `/query/retrieve` endpoint.
6. Add `/query/answer` endpoint.
7. Add debug mode for admins.

## Acceptance Criteria

* `mode=semantic` calls semantic engine only.
* `mode=navigation` calls navigation engine only.
* `mode=hybrid` calls both engines and merges evidence.
* `mode=auto` selects a mode based on query intent.
* API response clearly identifies which engine produced each evidence item.

---

# Phase 7 — Answer Composer and Citation Policy

## Goal

Generate grounded answers from retrieved evidence.

## Tasks

1. Add answer prompt builder.
2. Add citation formatter.
3. Add refusal/uncertainty behavior when evidence is weak.
4. Add answer endpoint.
5. Add tests for citation discipline.

## Acceptance Criteria

* Answers cite evidence.
* PageIndex evidence shows page/section when available.
* LightRAG evidence shows chunk/entity/relation metadata when available.
* No answer is generated without evidence unless the API explicitly allows general fallback.

---

# Phase 8 — Job Queue and Concurrent Indexing Safety

## Goal

Move indexing out of request lifecycle and make concurrent reads safe.

## Tasks

1. Add jobs table.
2. Add job worker.
3. Add queue abstraction.
4. Add per-document indexing lock.
5. Add index versioning.
6. Add retry failed job endpoint.
7. Add job status endpoint.

## Acceptance Criteria

* Upload returns quickly with job ID.
* Indexing runs in worker.
* Users can query active ready index while a new version is building.
* Failed indexing does not corrupt active index.
* Admin can inspect job status.

---

# Phase 9 — Admin Dashboard API and Observability

## Goal

Make the system operable.

## Tasks

1. Add audit logs.
2. Add query logs.
3. Add indexing logs.
4. Add token/cost tracking.
5. Add admin metrics endpoints.
6. Add slow query tracing.

## Acceptance Criteria

* Admin can see document/job/query status.
* Query logs show mode, engines used, latency, and cost.
* Indexing logs show phase-level progress.
* Errors are actionable.

---

# Phase 10 — Multi-User Hardening

## Goal

Prepare the app for 5–10 real users.

## Tasks

1. Add rate limits per user.
2. Add document ACLs if needed.
3. Add conversation history.
4. Add per-user query limits.
5. Add API key support if external apps need access.
6. Add backup/restore scripts.
7. Add deployment docs.

## Acceptance Criteria

* Multiple users can query concurrently.
* Admin writes do not block normal user reads.
* Unauthorized users cannot write or see restricted data.
* Basic backup/restore path exists.

---

# Phase 11 — Evaluation and Quality Gates

## Goal

Ensure retrieval quality improves instead of degrading.

## Tasks

1. Create small gold QA dataset.
2. Test semantic-only retrieval.
3. Test navigation-only retrieval.
4. Test hybrid retrieval.
5. Track answer faithfulness.
6. Track citation accuracy.
7. Add regression tests for important documents.

## Acceptance Criteria

* Evaluation script compares retrieval modes.
* Hybrid mode is not assumed better; it must be measured.
* Reindexing does not silently reduce answer quality.

---

## 20. Coding Agent Implementation Instructions

Use this instruction block with a coding agent.

```text
You are implementing a multi-user hybrid RAG application using FastAPI.

The application must combine:
1. LightRAG-style semantic/vector/graph retrieval.
2. PageIndex-style document tree/page-navigation retrieval.

Do not merge both engines into one giant class.
Build a clear layered architecture:
API routes → services → retrieval router → retrieval engines → adapters → external libraries/storage.

Important requirements:
- 5–10 user app.
- Authenticated users can query.
- Admin users can upload/index/delete/reindex.
- Normal users cannot write to the index.
- Retrieval must support semantic, navigation, hybrid, and auto modes.
- Both engines must return the same Evidence model.
- Query answers must cite Evidence.
- Indexing must run as a job, not block normal query requests.
- Keep the code senior-grade but junior-readable.

Implement phase by phase.
Do not jump ahead.
Each phase must include tests and docs.

Code style:
- explicit names
- small files
- small services
- no hidden global state
- no wildcard imports
- clear Pydantic schemas
- clear dataclasses/domain models
- structured logs
- docstrings on public interfaces

When adding an abstraction, explain in code comments why it exists.
If an abstraction has only one implementation and no clear future use, avoid it.
```

---

## 21. Junior Developer Reading Guide

A junior developer should read files in this order:

1. `docs/junior_dev_start_here.md`
2. `docs/architecture.md`
3. `domain/models.py`
4. `schemas/query.py`
5. `api/routes/query.py`
6. `services/retrieval_service.py`
7. `retrieval/router.py`
8. `retrieval/semantic_engine.py`
9. `retrieval/navigation_engine.py`
10. `integrations/lightrag_adapter.py`
11. `integrations/pageindex_adapter.py`
12. `workers/tasks.py`

The goal is that they can trace:

```text
HTTP query request
  → QueryRequest schema
  → route handler
  → retrieval service
  → retrieval router
  → engine
  → evidence
  → answer composer
  → QueryResponse
```

without needing to understand every internal detail of LightRAG or PageIndex on day one.

---

## 22. Final Architecture Recommendation

Build a merged product, not a merged blob.

The correct final design is:

```text
Multi-user FastAPI RAG application
  ├── Auth + RBAC
  ├── Document registry
  ├── Admin-only indexing pipeline
  ├── Shared parsed document model
  ├── PageIndex-style navigation index
  ├── LightRAG-style semantic index
  ├── Unified evidence model
  ├── Retrieval router
  ├── Answer composer
  ├── Job queue
  ├── Audit/query logs
  └── Admin observability APIs
```

This gives you the semantic retrieval strength of LightRAG and the document navigation strength of PageIndex while keeping the codebase readable and maintainable.
