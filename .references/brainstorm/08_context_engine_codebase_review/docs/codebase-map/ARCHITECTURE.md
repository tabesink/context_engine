# Architecture

## Current Architecture Summary

`context_engine` is structured as a backend-only RAG service with a clear separation between:

- API routes
- services/use cases
- retrieval engines
- LightRAG integration
- storage/repositories
- background jobs
- deployment/runtime config

The architecture is moving toward a clean layered system:

```text
client / WebUI / TUI
  → FastAPI route
  → auth/admin dependency
  → service layer
  → policy layer
  → retrieval engine or domain/document service
  → repository / adapter
  → PostgreSQL / Redis / file storage / remote LightRAG
  → response schema
```

## Runtime Topology

Typical local or production-like topology:

```text
Browser or API client
  → context_engine API container
      → PostgreSQL
      → Redis
      → RQ worker
      → status poller
      → file storage volume
      → remote LightRAG domain containers/services
```

## Main Boundaries

### API Boundary

The API layer should remain thin.

Responsibilities:

- validate request shape
- authenticate user
- enforce route-level admin/user access
- call services
- return response schemas

### Service Boundary

The service layer owns application workflows.

Examples:

- upload document
- delete document
- reingest document
- retrieve evidence
- list LightRAG domains
- start/stop/recreate domain
- build workspace tree

### Retrieval Boundary

The retrieval layer owns retrieval mechanics.

Current important concepts:

- remote LightRAG retrieval
- local rich navigation retrieval
- hybrid retrieval strategy
- evidence/citation mapping
- asset enrichment

### Integration Boundary

External systems should be behind adapters.

Important example:

```text
LightRAGRemoteAdapter
```

The app should call LightRAG through a stable internal interface, not from route handlers.

### Storage Boundary

Storage owns data persistence.

Important persisted categories:

- users
- documents
- processing jobs
- document structure
- pages
- sections
- blocks/chunks
- assets
- LightRAG domain metadata
- query/audit logs

## Recommended Target Architecture

```text
app/
  api/
    routes/
    schemas/
  core/
    config.py
    security.py
    deps.py
  services/
    document_service.py
    retrieval_service.py
    workspace_tree_service.py
    lightrag_domain_service.py
    policies/
      document_access_policy.py
      retrieval_access_policy.py
      domain_access_policy.py
  retrieval/
    strategies.py
    lightrag_remote_engine.py
    rich_navigation_engine.py
    evidence_mapper.py
    asset_enrichment.py
  integrations/
    lightrag_remote_adapter.py
    providers/
  storage/
    tables.py
    repositories/
  workers/
  scripts/
```

## Dependency Direction

Preferred direction:

```text
routes
  → services
  → policies / retrieval engines / repositories / adapters
  → infrastructure
```

Avoid:

```text
repositories → services
adapters → routes
retrieval engines → FastAPI dependencies
route handlers → direct external HTTP calls
```

## Request Flow: Retrieval

```text
POST /retrieve
  → authenticate user
  → parse RetrieveRequest
  → RetrievalService.retrieve()
  → validate requested LightRAG domain
  → resolve route/strategy
  → resolve authorized document set
  → call LightRAG remote retrieval and/or local navigation retrieval
  → map results to evidence objects
  → enrich with assets/images/tables when available
  → return RetrieveResponse
```

## Request Flow: Admin Upload

```text
POST /admin/documents/upload
  → require admin
  → validate file and domain
  → persist upload metadata
  → store raw file
  → enqueue processing/indexing job
  → worker processes document
  → local structure is stored
  → LightRAG domain ingestion is triggered or synchronized
  → job status is updated
```

## Important Design Principle

Remote LightRAG should remain a runtime integration boundary.

The app should not import LightRAG internals or duplicate LightRAG's semantic indexing engine. It should own:

- users
- auth
- document metadata
- structured navigation
- domain lifecycle metadata
- retrieval orchestration
- API contract
- evidence response shape

LightRAG should own:

- semantic/vector/graph retrieval internals
- its own graph/vector/document-status storage
- model/provider execution as configured for that domain
