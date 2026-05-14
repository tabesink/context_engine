# Task: Review and Refine the Lean LightRAG Integration Plan for `context_engine`

## Role

You are a senior software architect and implementation-focused coding agent.

You are working on the `context_engine` master codebase. Your first responsibility is **not to code immediately**. Your first responsibility is to inspect the existing codebase, understand the current architecture, and determine whether the brainstormed lean LightRAG integration plan fits the real implementation.

## Core Objective

Extend `context_engine` so it can use an independently deployed, lean LightRAG service for:

1. context retrieval
2. semantic/vector/graph retrieval
3. graph visualization APIs

The goal is **not** to merge LightRAG into `context_engine`.

The correct boundary is:

```text
context_engine = master multi-user application / orchestration layer
external/lightrag = lean retrieval + graph engine
````

Communication between `context_engine` and LightRAG must happen through HTTP only.

## Architectural Rule

LightRAG is the retrieval engine.

`context_engine` is the multi-user application layer.

Therefore:

```text
context_engine must not import LightRAG internals.
context_engine must not vendor the LightRAG source into app/.
context_engine must not duplicate LightRAG graph/vector storage.
context_engine must not copy the full easy-deploy-lightrag app.
```

## Inputs to Review

Review the existing `context_engine` codebase and the provided brainstormed plan.

Use the brainstormed plan as a proposal, not as guaranteed truth.

You must inspect the real codebase and answer:

1. Does this plan fit the current `context_engine` architecture?
2. Where does it align cleanly?
3. Where will it create friction?
4. Which files/modules already exist and should be reused?
5. Which proposed files are unnecessary because the codebase already has an equivalent?
6. Which parts of the plan should be simplified?
7. Which parts must be implemented differently because of the current codebase?
8. What is the lowest-entropy implementation path?

## Current Desired Architecture

`context_engine` should own:

```text
users
auth
RBAC/admin permissions
admin-only upload authorization
document mirror records
retrieval settings/profiles
query routes
answer/citation pipeline
graph proxy routes
audit logs
query logs
job/status records
```

External LightRAG should own:

```text
document ingestion/indexing
semantic/context retrieval
vector retrieval
graph/entity/relation retrieval
graph storage
graph visualization data
LightRAG storage internals
```

## Hard Constraints

Do not:

```text
copy the full easy-deploy-lightrag server into context_engine
copy LightRAG WebUI
copy the client folder
copy auth/conversation/SQLite app-control logic
add a second user/auth system inside LightRAG
import LightRAG internals from context_engine/app
store graph nodes/edges in context_engine v1
add Neo4j to context_engine
implement PageIndex in this task
implement local semantic indexing in this task
implement LLM query routing in this task
build a large abstraction framework before proving the boundary
```

Do:

```text
inspect current context_engine structure first
identify existing routes/services/models/repositories
reuse existing auth/RBAC/document/query patterns
add one clear LightRAG HTTP adapter
add or reuse a domain manifest reader
add or reuse admin-only upload flow
forward admin uploads to external LightRAG
add context retrieval through external LightRAG
add graph proxy/normalization routes
add retrieval settings using env defaults + optional JSONB profile
add contract files for the LightRAG HTTP boundary
add tests using mocked LightRAG responses
document all friction and deviations from the brainstormed plan
```

## Reference Direction

The desired lean integration is:

```text
POST /query/retrieve
  → existing query route or retrieval service
  → LightRAGRemoteAdapter.retrieve_context()
  → external LightRAG /query/context
  → normalized Evidence[]
```

Admin upload should be:

```text
admin uploads file to context_engine
context_engine checks require_admin
context_engine creates/updates local document mirror record
context_engine forwards file to external LightRAG over HTTP
LightRAG indexes the document
context_engine stores external_document_id, domain, status
context_engine records audit/job status
```

Graph access should be:

```text
authenticated user requests graph from context_engine
context_engine calls external LightRAG graph endpoint
context_engine normalizes response for frontend
context_engine does not persist graph nodes/edges in v1
```

## Required First Pass: Codebase Fit Review

Before implementing anything, produce a short architecture review with these sections:

### 1. Existing `context_engine` Architecture Map

Identify current folders/files for:

```text
FastAPI app startup
settings/config
auth/RBAC
document routes
query routes
retrieval service
document models/tables
job/status handling
audit/query logging
integration/adapters
tests
```

### 2. Plan Fit Assessment

For each proposed component, classify as:

```text
KEEP AS-IS
MODIFY TO FIT EXISTING CODE
REUSE EXISTING CODE
DEFER
REMOVE
```

Components to assess:

```text
LightRAGRemoteAdapter
domain manifest reader
contract files
admin upload forwarding
document mirror fields
query retrieval flow
graph proxy routes
retrieval settings
JSONB retrieval profiles
deploy-lightrag.sh wrapper
mocked integration tests
observability logs
```

### 3. Friction / Risk Analysis

Identify specific friction points, including:

```text
existing route names may differ from proposed route names
existing document model may not match proposed mirror fields
existing retrieval flow may already have abstractions
existing auth dependency may use different role names
existing DB may already have tables/migrations
LightRAG API may not match proposed /query/context contract
domain manifest fallback may hide broken deployments
upload indexing may need async job handling
graph response shape may need normalization
tests may need existing fixture style
```

### 4. Leanest Implementation Path

Propose the smallest set of changes that achieves the goal without adding entropy.

Prefer:

```text
one adapter file
one settings section
one contract file
one upload forwarding path
one graph proxy module
one retrieval settings merge function
mocked tests
small documentation update
```

Avoid:

```text
large new frameworks
duplicated services
parallel auth systems
parallel document registries
premature PageIndex integration
premature hybrid merger
premature graph persistence
```

## Implementation Plan After Review

Only after completing the fit review, produce an implementation plan.

The plan must include:

```text
Phase 0 — Codebase alignment and docs
Phase 1 — LightRAG contract files
Phase 2 — settings + domain manifest reader
Phase 3 — LightRAGRemoteAdapter
Phase 4 — retrieval path integration
Phase 5 — admin upload forwarding
Phase 6 — graph proxy routes
Phase 7 — retrieval settings/profile merge
Phase 8 — tests with mocked LightRAG
Phase 9 — README/.env/deployment documentation
```

For each phase include:

```text
files to inspect
files to modify
files to create
expected behavior
tests to add
acceptance criteria
rollback risk
```

## LightRAG Contract Target

Use this as the desired external contract unless the real LightRAG API requires a shim:

```text
GET  /health
POST /documents/upload
GET  /documents/{id}/status
POST /query/context
GET  /graph
GET  /document-graph
```

Optional:

```text
GET /graph/documents/{document_id}
GET /graph/entities
GET /graph/relationships
```

If upstream LightRAG does not expose this shape directly, create only a tiny compatibility shim under:

```text
external/lightrag/shim/
```

The shim may normalize request/response shapes only.

The shim must not own:

```text
users
auth
conversations
dashboards
application state
SQLite control plane
```

## Storage Decision

Use this storage boundary:

```text
Postgres:
  context_engine users
  roles
  document mirror records
  retrieval profiles
  jobs
  audit logs
  query logs
  conversations if enabled

JSON:
  external/lightrag/data/domains.json only
  deployment/domain metadata only

Neo4j:
  not in context_engine
  only inside external LightRAG if LightRAG requires it

Redis:
  optional for context_engine jobs/cache
```

For 5–10 users, do not use JSON files for mutable app runtime state.

## Required Tests

Add tests according to the existing test style.

No test should require a live LightRAG service.

Test at minimum:

```text
LightRAG timeout
LightRAG 500 response
LightRAG invalid JSON
domain manifest fallback
domain manifest health check
retrieval settings merge order
query route maps LightRAG results to Evidence
non-admin upload receives 403
admin upload is forwarded to LightRAG
document mirror stores external document metadata
graph proxy normalizes nodes/edges
graph proxy does not write graph data to context_engine DB
```

## Required Output Before Coding

Before making code changes, output:

```text
1. Current architecture map
2. Fit/friction review
3. Refined implementation plan
4. Files to modify/create
5. Risks and simplifications
6. Final acceptance criteria
```

## Final Acceptance Criteria

The task is complete only when:

```text
context_engine uses external LightRAG for production context retrieval
context_engine imports no LightRAG internals
external/lightrag remains deployment + contract + optional shim only
only admins can upload/index/delete/reindex
uploads are forwarded to external LightRAG over HTTP
regular users can query concurrently
graph APIs are proxied through context_engine
retrieval settings are configurable
Postgres stores context_engine runtime state
JSON is used only for LightRAG deployment/domain manifests
Neo4j is not added to context_engine
tests pass without a live LightRAG service
LightRAG can be updated/redeployed independently
documentation explains the boundary clearly
```

## Bias Toward Simplicity

When in doubt, choose the implementation that keeps the boundary obvious to a junior developer:

```text
API route
  → service
  → LightRAGRemoteAdapter
  → HTTP contract
  → Evidence[]
```

Do not add abstractions unless they remove real duplication or isolate real external volatility.

```
```
