# Context Engine Codebase Review Documentation Package



---

# README


# Context Engine Codebase Map Documentation Package

Generated: 2026-05-26

This documentation package is a repo-ready architecture and codebase review set for:

```text
https://github.com/tabesink/context_engine.git
```

It is intended for:

- junior developers
- coding agents
- future maintainers
- frontend integration work
- backend API review
- LightRAG/domain lifecycle work
- production-hardening planning

## How to Use This Package

Place this folder into the repository at:

```text
docs/codebase-map/
```

Recommended reading order:

1. `CODEBASE_INDEX.md`
2. `ARCHITECTURE.md`
3. `RAG_PIPELINE.md`
4. `API_MAP.md`
5. `DATABASE_AND_STORAGE_SCHEMA.md`
6. `CONFIGURATION_AND_DEPLOYMENT.md`
7. `ARCHITECTURE_REVIEW.md`
8. `REFACTORING_ROADMAP.md`
9. `CODING_AGENT_GUIDE.md`
10. `ADRS_TO_WRITE.md`

## Important Review Position

This review does **not** recommend rewriting the system.

The current architecture is moving in a good direction:

```text
FastAPI backend
  → PostgreSQL app state
  → Redis/RQ background jobs
  → remote LightRAG semantic retrieval
  → local document navigation retrieval
  → single /retrieve evidence API
```

The main recommendation is to make the architecture easier to understand, safer to operate, and clearer for frontend integration.

## Top Recommendations

1. Document the shared-corpus access model as an intentional architecture decision.
2. Resolve the CLI/TUI support contradiction in project docs.
3. Pin LightRAG container images in staging/production.
4. Add a small `RetrievalAccessPolicy` before deeper frontend integration.
5. Keep `/retrieve` as the single evidence/retrieval API.



---

# CODEBASE_INDEX


# Codebase Index

## Repository Purpose

`context_engine` appears to be a backend-only, multi-user hybrid RAG application. Its primary job is to provide authenticated API access to document ingestion, retrieval, workspace navigation, and LightRAG domain lifecycle management.

The application is designed around:

- FastAPI routes
- PostgreSQL-backed application state
- Redis/RQ background jobs
- remote LightRAG as the semantic retrieval engine
- local structured document navigation
- admin-only write operations
- regular-user retrieval/query operations

## Important Root-Level Files

```text
README.md
AGENTS.md
pyproject.toml
docker-compose.yml
Dockerfile
alembic.ini
```

### `README.md`

Primary human-facing project overview.

Important because it describes:

- backend-only RAG purpose
- local development commands
- Docker Compose usage
- API behavior
- TUI/CLI workflow, if still supported

### `AGENTS.md`

Instructions for future coding agents.

Important because it may override developer assumptions. At the time of review, this file conflicted with the README about whether CLI/TUI is supported.

### `pyproject.toml`

Dependency and tooling manifest.

Important because it confirms the actual stack:

- FastAPI
- Uvicorn
- SQLAlchemy
- Alembic
- PostgreSQL driver
- Redis/RQ
- Pydantic settings
- HTTPX
- JWT/auth libraries
- pytest
- Ruff

### `docker-compose.yml`

Local/runtime orchestration.

Important because it defines:

- API service
- worker service
- status poller
- PostgreSQL
- Redis
- migration service
- volumes
- ports
- service startup order

## Main Application Folders

Expected important folders:

```text
app/
  api/
    routes/
  core/
  integrations/
  retrieval/
  services/
  storage/
  workers/
tests/
docs/
alembic/
```

## Suggested Reading Path for Junior Developers

### 1. Application entry point

Start with:

```text
app/main.py
```

Learn:

- how the FastAPI app is created
- which routers are registered
- how CORS is configured
- which endpoints exist at a high level

### 2. API routes

Read:

```text
app/api/routes/retrieve.py
app/api/routes/documents.py
app/api/routes/admin.py
app/api/routes/lightrag.py
app/api/routes/lightrag_admin.py
app/api/routes/workspace_tree.py
app/api/routes/jobs.py
app/api/routes/health.py
```

Learn:

- which operations are user-facing
- which operations are admin-only
- which routes call which services

### 3. Retrieval orchestration

Read:

```text
app/services/retrieval_service.py
app/retrieval/strategies.py
app/retrieval/lightrag_remote_engine.py
app/retrieval/rich_navigation_engine.py
```

Learn:

- how retrieval mode is selected
- when remote LightRAG is used
- when local navigation retrieval is used
- how evidence is assembled

### 4. LightRAG boundary

Read:

```text
app/integrations/lightrag_remote_adapter.py
app/services/lightrag_domain_service.py
app/services/lightrag_domain_registry.py
```

Learn:

- how LightRAG is kept outside the app as an HTTP service
- how domains are listed/resolved
- how lifecycle actions are handled

### 5. Storage and data model

Read:

```text
app/storage/tables.py
app/storage/repositories/
alembic/
```

Learn:

- what entities exist
- how documents, pages, sections, chunks, assets, jobs, and logs are stored
- where migrations are defined

### 6. Auth and settings

Read:

```text
app/core/config.py
app/core/security.py
app/core/deps.py
```

Learn:

- how configuration is loaded
- how JWTs are handled
- how admin/user permissions are enforced
- what production guardrails exist

## What Belongs Where

### `app/api/routes/`

Owns HTTP request/response concerns.

Should contain:

- route definitions
- request validation via schemas
- dependency injection
- calls into services

Should not contain:

- direct database business logic
- LightRAG HTTP implementation details
- file-system cleanup logic
- indexing algorithms

### `app/services/`

Owns application use cases.

Should contain:

- document upload orchestration
- retrieval orchestration
- domain lifecycle orchestration
- workspace-tree assembly
- policy coordination

Should not contain:

- raw HTTP route concerns
- direct frontend formatting logic
- low-level adapter implementation details where avoidable

### `app/retrieval/`

Owns retrieval engines and strategies.

Should contain:

- LightRAG semantic retrieval engine
- local navigation retrieval engine
- hybrid strategy logic
- evidence mapping
- retrieval ranking/merging behavior

Should not contain:

- admin upload logic
- user-management logic
- hard-coded HTTP routes

### `app/integrations/`

Owns external system adapters.

Should contain:

- LightRAG HTTP adapter
- future provider adapters
- external service clients

Should not contain:

- domain business rules
- route-level auth logic

### `app/storage/`

Owns persistence models and repository access.

Should contain:

- SQLAlchemy tables
- repository classes
- persistence-specific query helpers

Should not contain:

- route handlers
- provider calls
- UI-specific response shaping

## Areas to Be Careful With

- `app/core/config.py`
- `app/services/retrieval_service.py`
- `app/retrieval/rich_navigation_engine.py`
- `app/retrieval/lightrag_remote_engine.py`
- `app/integrations/lightrag_remote_adapter.py`
- `app/api/routes/admin.py`
- `app/api/routes/lightrag_admin.py`
- Alembic migrations
- Docker Compose service names, ports, volumes, and commands

## Current Documentation Gap

The repo should clearly state whether CLI/TUI is:

1. supported developer harness,
2. deprecated legacy code, or
3. product-supported interface.

At the time of review, README and coding-agent guidance appeared to conflict on this point.



---

# ARCHITECTURE


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



---

# PRD


# Product Requirements Document

## 1. Product Purpose

`context_engine` is a backend service for a multi-user hybrid RAG application.

Its purpose is to let authenticated users query a shared knowledge corpus while admins manage document ingestion, document lifecycle, and LightRAG domain lifecycle.

## 2. Target Users

### Admin Users

Admins can:

- upload documents
- reingest documents
- delete/archive documents
- manage LightRAG domains
- start/stop/recreate domain services
- view indexing/job status
- configure or operate backend infrastructure

### Regular Users

Regular authenticated users can:

- list available retrieval domains
- submit retrieval requests
- receive evidence/citation results
- navigate the shared workspace tree
- inspect document/page/section-level evidence if exposed by frontend

### Developers / Coding Agents

Developers need:

- clear API map
- clear service boundaries
- predictable folder structure
- safe refactoring guidance
- documentation for retrieval and storage behavior

## 3. Core Use Cases

### UC1: Admin uploads a document

An admin uploads a document into a selected LightRAG domain. The system stores the file, tracks processing state, indexes structured document information locally, and sends the relevant content to LightRAG.

### UC2: User retrieves evidence

A user selects or defaults to a LightRAG domain and asks a plain-language question. The backend returns evidence from remote LightRAG and/or local navigation retrieval.

### UC3: User browses workspace tree

A user opens a workspace tree showing documents and document structure aligned with the selected domain.

### UC4: Admin manages LightRAG domain lifecycle

An admin creates, starts, stops, deletes, recreates, or regenerates a LightRAG domain deployment.

### UC5: Developer validates API flows

A developer or coding agent uses tests, API routes, and possibly the TUI/CLI harness to validate backend behavior before frontend integration.

## 4. Functional Requirements Implemented or Expected

| Requirement | Status | Notes |
|---|---|---|
| User authentication | Implemented | JWT/bearer-token style auth |
| Admin authorization | Implemented | Admin-only dependencies/routes |
| Document upload | Implemented | Admin route |
| Document listing | Implemented | User-readable metadata |
| Document structure retrieval | Implemented | Pages/sections/chunks/assets |
| Remote LightRAG retrieval | Implemented | Mandatory semantic backend |
| Local navigation retrieval | Implemented | Structured lookup |
| Single retrieve API | Implemented | `/retrieve` should remain canonical |
| LightRAG domain list | Implemented | User-readable domain summaries |
| LightRAG lifecycle management | Implemented/partial | Admin routes |
| Background processing | Implemented | Redis/RQ pattern |
| Workspace tree | Implemented/partial | Exposed for frontend integration |
| Query/audit logging | Implemented/partial | Privacy-oriented config exists |

## 5. Non-Functional Requirements

### Reliability

- Avoid silent fallback to local semantic retrieval.
- Surface LightRAG domain health clearly.
- Ensure indexing jobs are retryable or recoverable.
- Avoid losing uploaded files or domain state during delete/archive operations.

### Security

- Admin-only write operations.
- Regular users are read-only for shared corpus.
- Production weak secrets should be rejected.
- Wildcard CORS should not be allowed in production.
- Document shared-corpus behavior explicitly.

### Maintainability

- Keep route handlers thin.
- Keep retrieval engines modular.
- Keep LightRAG behind an adapter.
- Avoid duplicate query APIs.
- Keep settings readable and grouped.

### Observability

- Track job status.
- Track LightRAG health.
- Track retrieval route/mode.
- Log query metadata without storing raw text by default.
- Add cost/provider tracing later if LLM provider costs matter.

### Scalability

Designed scale appears to be small-team internal use, roughly 5–10 users. Current architecture is appropriate for this scale. If corpus size grows substantially, local navigation retrieval may need PostgreSQL full-text search or a precomputed search index.

## 6. Current Product Clarifications Needed

1. Is the corpus intentionally shared across all authenticated users?
2. Is CLI/TUI supported or deprecated?
3. Are LightRAG domains user-selectable by all users?
4. Should archived domain documents and associated assets be hard-deleted or retained?
5. Is production deployment expected to manage LightRAG containers locally or connect to externally managed LightRAG services?

## 7. Future Requirements

Potential future capabilities:

- per-domain access grants
- per-document visibility scopes
- provider profile management
- Bedrock OpenAI-compatible provider config
- frontend evidence panel with image/table cards
- retrieval evaluation datasets
- Langfuse or similar observability integration
- PostgreSQL full-text navigation search
- structured backup/restore tooling



---

# API_MAP


# API Map

## API Design Summary

The backend should expose a small, clear API surface:

```text
/auth/*
/documents/*
/admin/documents/*
/retrieve
/lightrag/*
/admin/lightrag/*
/workspace-tree/*
/jobs/*
/health/*
```

The most important design choice is to keep `/retrieve` as the canonical retrieval/evidence endpoint.

Avoid adding duplicate query endpoints unless there is a distinct, well-documented product need.

## Authentication APIs

Expected owner:

```text
app/api/routes/auth.py
```

Typical responsibilities:

- login
- issue bearer token
- identify current user
- support admin/user role checks through dependencies

Important architecture rule:

Auth route should not contain document, retrieval, or LightRAG logic.

## Health APIs

Expected owner:

```text
app/api/routes/health.py
```

Typical endpoints:

```text
GET /health
GET /health/readiness
```

Typical checks:

- API process alive
- database reachable
- Redis reachable
- LightRAG availability where relevant
- worker/status-poller assumptions where relevant

## Documents APIs

Expected owner:

```text
app/api/routes/documents.py
```

Likely user-readable operations:

```text
GET /documents
GET /documents/{document_id}
GET /documents/{document_id}/structure
GET /documents/{document_id}/pages
GET /documents/{document_id}/sections
GET /documents/{document_id}/chunks
GET /documents/{document_id}/assets
GET /documents/{document_id}/thumbnail
```

Responsibilities:

- expose document metadata
- expose ready document structure
- expose page/section/chunk/asset information
- enforce authenticated read access

Important rule:

Document read APIs should use `DocumentAccessPolicy` or equivalent.

## Admin Document APIs

Expected owner:

```text
app/api/routes/admin.py
```

Likely admin-only operations:

```text
POST /admin/documents/upload
POST /admin/documents/{document_id}/reingest
DELETE /admin/documents/{document_id}
```

Responsibilities:

- upload files
- create processing jobs
- reingest documents
- archive/delete documents
- enforce admin-only write access

Important rule:

Do not allow regular authenticated users to modify corpus state.

## Retrieval API

Expected owner:

```text
app/api/routes/retrieve.py
```

Canonical endpoint:

```text
POST /retrieve
```

Expected request concepts:

```json
{
  "query": "plain-language question",
  "lightrag_domain_id": "optional-selected-domain",
  "document_ids": ["optional-document-filter"],
  "mode": "optional-retrieval-mode",
  "top_k": 10,
  "include_assets": true
}
```

Expected response concepts:

```json
{
  "answer": "optional, if answer composition is enabled",
  "evidence": [
    {
      "reference_id": "stable citation id",
      "document_id": "document id",
      "document_title": "title",
      "source_path": "path or filename",
      "chunk_id": "chunk id",
      "page_number": 1,
      "score": 0.87,
      "text": "evidence text",
      "metadata": {},
      "assets": []
    }
  ],
  "metadata": {
    "retrieval_mode": "hybrid",
    "lightrag_domain_id": "domain"
  }
}
```

Important design rule:

`/retrieve` should return evidence in a frontend-stable shape. The frontend should not parse deeply nested LightRAG-specific metadata for core display fields.

## LightRAG Domain APIs

Expected owner:

```text
app/api/routes/lightrag.py
```

User-readable operations:

```text
GET /lightrag/domains
```

Responsibilities:

- list available domains
- expose safe domain metadata
- avoid exposing secrets or container internals

## Admin LightRAG Lifecycle APIs

Expected owner:

```text
app/api/routes/lightrag_admin.py
```

Admin-only operations may include:

```text
POST /admin/lightrag/domains
POST /admin/lightrag/domains/{domain_id}/start
POST /admin/lightrag/domains/{domain_id}/stop
POST /admin/lightrag/domains/{domain_id}/recreate
POST /admin/lightrag/domains/{domain_id}/regenerate
DELETE /admin/lightrag/domains/{domain_id}
```

Responsibilities:

- manage domain lifecycle
- manage deployment metadata
- manage container lifecycle where applicable
- update domain registry/manifest
- protect all writes with admin auth

## Workspace Tree APIs

Expected owner:

```text
app/api/routes/workspace_tree.py
```

Likely endpoint:

```text
GET /workspace-tree
```

or domain-scoped:

```text
GET /workspace-tree?lightrag_domain_id={domain_id}
```

Responsibilities:

- expose a tree suitable for frontend navigation
- group documents by selected domain
- include pages/sections/assets if appropriate
- avoid returning excessive content by default

## Jobs APIs

Expected owner:

```text
app/api/routes/jobs.py
```

Likely operations:

```text
GET /jobs
GET /jobs/{job_id}
```

Responsibilities:

- expose indexing/upload job state
- show processing errors
- help debug ingestion/reingestion workflows

## API Rules for Future Work

1. Do not create duplicate query endpoints.
2. Keep `/retrieve` as the canonical evidence API.
3. Keep write operations under admin routes.
4. Keep LightRAG internals hidden behind backend API contracts.
5. Keep response fields stable for frontend integration.
6. Use explicit top-level evidence fields for common display needs:
   - `source_path`
   - `document_title`
   - `chunk_id`
   - `reference_id`
   - `page_number`
   - `assets`



---

# DATABASE_AND_STORAGE_SCHEMA


# Database and Storage Schema

## Storage Overview

The system uses several categories of storage:

```text
PostgreSQL
  → app metadata and relational document structure

Redis
  → background job queue / worker coordination

File storage
  → uploaded source files
  → extracted assets such as images/tables/thumbnails

LightRAG domain storage
  → semantic/vector/graph/index data owned by LightRAG

Logs/audit/query metadata
  → operational/debugging records
```

## PostgreSQL Responsibilities

PostgreSQL should own application state, not LightRAG internals.

Expected persisted concepts:

- users
- roles/admin flags
- documents
- document processing status
- pages
- sections
- blocks
- chunks
- assets
- jobs
- LightRAG domain metadata/manifest entries
- audit/query logs

## Recommended Conceptual Schema

### Users

```text
users
  id
  email
  hashed_password
  is_active
  is_admin
  created_at
  updated_at
```

### Documents

```text
documents
  id
  title
  source_path
  original_filename
  lightrag_domain_id
  status
  uploaded_by_user_id
  created_at
  updated_at
  archived_at
  deleted_at
```

Important rule:

Each document should belong to exactly one LightRAG domain.

### Document Pages

```text
document_pages
  id
  document_id
  page_number
  text
  width
  height
  metadata
```

### Document Sections

```text
document_sections
  id
  document_id
  parent_section_id
  title
  level
  page_start
  page_end
  order_index
  metadata
```

### Document Chunks

```text
document_chunks
  id
  document_id
  section_id
  page_number
  text
  token_count
  order_index
  metadata
```

### Document Assets

```text
document_assets
  id
  document_id
  page_number
  chunk_id
  asset_type
  storage_path
  thumbnail_path
  caption
  metadata
```

Asset types may include:

- image
- table
- chart
- figure
- thumbnail

### Processing Jobs

```text
processing_jobs
  id
  document_id
  job_type
  status
  error_message
  attempts
  created_at
  started_at
  completed_at
```

### LightRAG Domains

```text
lightrag_domains
  id
  name
  status
  base_url
  storage_path
  container_name
  created_at
  updated_at
  last_health_check_at
```

Actual implementation may use a manifest-backed registry instead of only relational rows. The important architectural point is that domain metadata must have a single source of truth.

## File Storage Responsibilities

File storage should contain:

```text
.data/
  uploads/
  assets/
  thumbnails/
  lightrag/
    domains/
```

Recommended separation:

```text
uploaded source document
  → immutable original file

parsed assets
  → generated from original file

LightRAG domain data
  → managed by LightRAG lifecycle operations
```

## Delete vs Archive Policy

Important unresolved product decision:

When an admin archives or deletes a document/domain, what happens to associated files?

Need to define behavior for:

- uploaded source file
- extracted images
- extracted tables
- thumbnails
- local structured rows
- LightRAG indexed chunks
- LightRAG graph/vector data
- audit/query logs referencing the document

Recommended V1 policy:

```text
Archive:
  - hide from normal retrieval
  - keep source files and assets
  - keep audit/query records
  - retain recovery path

Hard delete:
  - admin-only destructive operation
  - remove local rows
  - remove uploaded files and generated assets
  - remove or rebuild LightRAG domain index
  - write audit record
```

For multi-user shared corpus, hard delete should be very explicit because it affects all users.

## Redis Responsibilities

Redis should be treated as operational infrastructure.

Owns:

- queued jobs
- worker coordination
- transient job state if RQ uses Redis state
- possibly status polling coordination

Redis should not be the only durable source for business-critical metadata.

## LightRAG Storage Responsibilities

LightRAG owns semantic retrieval internals.

This may include:

- vector index
- graph index
- key-value/index metadata
- document status storage
- cache storage
- provider-specific artifacts

Important rule:

Do not make the main app depend on LightRAG internal storage schema. Communicate through LightRAG API/adapter boundaries.

## Backup and Restore Considerations

Production backup should include:

- PostgreSQL database
- uploaded files
- generated assets if expensive to regenerate
- LightRAG domain storage directories
- domain manifest/registry
- `.env` or deployment secrets through secure secret manager

Do not rely on database backup alone if uploaded files and LightRAG domain data live on mounted volumes.

## Storage Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Uploaded files retained after domain deletion unintentionally | Medium/High | Define archive/delete policy |
| LightRAG data deleted without local metadata update | High | Lifecycle operations should be transactional or compensating |
| Domain manifest and DB disagree | High | Use one source of truth or reconciliation job |
| Asset paths break after moving storage root | Medium | Store relative paths and centralize storage config |



---

# CONFIGURATION_AND_DEPLOYMENT


# Configuration and Deployment

## Runtime Components

Expected runtime stack:

```text
API container
PostgreSQL container/service
Redis container/service
RQ worker container
status-poller container
migration service
LightRAG domain containers/services
file storage volumes
```

## Startup Flow

Recommended startup flow:

```text
docker compose up
  → PostgreSQL starts
  → Redis starts
  → migration service runs alembic upgrade head
  → API starts after migrations complete
  → worker starts after migrations complete
  → status poller starts after migrations complete
  → API health/readiness becomes available
```

## Environment Variable Categories

### Core App

```text
ENVIRONMENT
APP_NAME
API_HOST
API_PORT
```

### Security

```text
SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES
SEED_ADMIN_EMAIL
SEED_ADMIN_PASSWORD
```

Production guardrails should reject:

- default/weak `SECRET_KEY`
- weak seed admin password
- insecure production values

### CORS

```text
ALLOWED_ORIGINS
```

Production should reject wildcard origins.

Recommended examples:

```text
http://localhost:3000
https://your-frontend.example.com
```

### Database

```text
DATABASE_URL
```

Production should use PostgreSQL, not SQLite.

SQLite should be allowed only for isolated tests.

### Redis / Queue

```text
REDIS_URL
RQ_QUEUE_NAME
```

### Storage

```text
DATA_DIR
UPLOADS_DIR
ASSETS_DIR
```

Keep all storage paths centralized.

### LightRAG Runtime

```text
LIGHTRAG_ENABLED
LIGHTRAG_BASE_URL
LIGHTRAG_DOMAIN
```

Recommended product posture:

- `LIGHTRAG_ENABLED=true` for normal runtime
- no local semantic fallback
- retrieval fails clearly if LightRAG/domain is unavailable

### LightRAG Domain Deployment

```text
LIGHTRAG_DEPLOY_ENABLED
LIGHTRAG_IMAGE
LIGHTRAG_DOMAIN_ROOT
LIGHTRAG_PORT_BASE
```

Important production rule:

Do not use `:latest` image tags in staging or production.

### Provider/API Keys

```text
OPENAI_API_KEY
OPENAI_BASE_URL
OPENAI_MODEL
EMBEDDING_MODEL
```

For OpenAI-compatible Bedrock endpoints, prefer provider profile settings rather than scattering provider-specific logic across services.

## Production Guardrails

Recommended validations:

```text
Reject weak/default SECRET_KEY in production
Reject wildcard CORS in production
Reject SQLite in production
Reject weak seed admin password in production
Reject LIGHTRAG_IMAGE=:latest in production
Require intentional LIGHTRAG_DEPLOY_ENABLED posture
Require explicit external origins
```

## Docker Compose Notes

Good Compose design should include:

- isolated services
- named volumes
- explicit health checks
- migration service
- API depends on migrations
- worker depends on migrations
- Redis and Postgres health checks
- clear port mappings
- persistent volumes for database and file data

## Deployment Risks

### Risk: Image drift

Using `latest` LightRAG image can silently change behavior.

Mitigation:

```text
Pin image tags in staging/production.
Document upgrade steps.
Run retrieval smoke tests after bumping LightRAG version.
```

### Risk: Mixed frontend/backend URL configuration

If frontend is HTTPS but backend URL is HTTP, browsers will block requests.

Mitigation:

```text
Use HTTPS backend URL in frontend config.
Configure CORS with exact frontend origin.
```

### Risk: Migrations not applied before API start

Mitigation:

```text
Keep migration service or deploy pre-command.
Block API start until migrations succeed.
```

### Risk: Secrets checked into `.env.example`

Mitigation:

```text
Keep `.env.example` placeholder-only.
Never commit real API keys.
Use deployment secret manager.
```

## Recommended Deployment Checklist

Before production:

- [ ] PostgreSQL database configured
- [ ] Redis configured
- [ ] migrations run successfully
- [ ] admin seed user configured with strong password
- [ ] `SECRET_KEY` strong and unique
- [ ] CORS origins exact, not wildcard
- [ ] LightRAG image pinned
- [ ] LightRAG domain storage backed by persistent volume
- [ ] uploaded file storage backed by persistent volume
- [ ] health/readiness endpoints pass
- [ ] worker is running
- [ ] status poller is running
- [ ] `/retrieve` smoke test passes
- [ ] admin upload smoke test passes
- [ ] domain lifecycle smoke test passes, if deployment management is enabled



---

# RAG_PIPELINE


# RAG Pipeline

## Pipeline Summary

The system is a hybrid RAG backend with two complementary retrieval paths:

1. Remote LightRAG semantic retrieval
2. Local structured document navigation retrieval

Recommended conceptual flow:

```text
source document
  → upload
  → parse/extract
  → normalized document structure
  → local pages/sections/chunks/assets
  → LightRAG ingestion
  → retrieval request
  → semantic retrieval and/or navigation retrieval
  → evidence/citation response
```

## Ingestion Flow

```text
admin uploads file
  → API validates admin
  → DocumentService stores original file
  → document metadata row is created
  → processing job is queued
  → worker parses document
  → pages/sections/chunks/assets are stored locally
  → content is sent to LightRAG domain
  → processing status is updated
```

## Local Structured Model

The local model should preserve:

- document identity
- page numbers
- section hierarchy
- chunk text
- chunk-to-page mapping
- chunk-to-section mapping
- assets such as images/tables
- source path/title metadata

This enables frontend features such as:

- workspace tree
- document outline
- page navigation
- right-side evidence panel
- citations that link to document/page/chunk
- image/table evidence cards

## Semantic Retrieval

Remote LightRAG should handle:

- semantic/vector retrieval
- graph retrieval
- hybrid graph-vector retrieval
- LightRAG-specific storage
- LightRAG provider/model behavior

The backend should treat LightRAG as an external service.

Internal code should communicate through:

```text
LightRAGRemoteAdapter
```

or equivalent.

## Navigation Retrieval

Local navigation retrieval should handle:

- document title matching
- section/page/chunk keyword lookup
- asset lookup
- workspace/tree navigation
- known document/page/section references
- exact-ish local evidence discovery

Important naming rule:

Call this **navigation retrieval** or **structured lookup**, not full semantic search.

## Hybrid Retrieval

Hybrid retrieval should:

```text
semantic evidence from LightRAG
  + local navigation evidence
  → normalize
  → deduplicate
  → rank/merge
  → enrich with local metadata/assets
  → return stable evidence objects
```

## Evidence Object

Recommended stable evidence fields:

```json
{
  "reference_id": "E1",
  "source_path": "uploads/file.pdf",
  "document_id": "doc_123",
  "document_title": "Document title",
  "chunk_id": "chunk_456",
  "section_id": "section_789",
  "page_number": 12,
  "score": 0.82,
  "text": "Evidence text",
  "asset_ids": ["asset_1"],
  "assets": [
    {
      "asset_id": "asset_1",
      "type": "image",
      "url": "/documents/doc_123/assets/asset_1",
      "caption": "Figure 2"
    }
  ],
  "metadata": {}
}
```

## Asset Enrichment

When evidence maps to a chunk/page/section, the backend should be able to attach relevant assets:

```text
evidence chunk
  → local chunk_id/page_number
  → nearby assets/images/tables
  → compact asset metadata
  → frontend renders evidence card
```

Asset enrichment should be optional because it may increase response size.

## Frontend Evidence Panel Support

Recommended compact citation map:

```text
[E1] Document Title · p. 12 · Section 3.2
     Evidence snippet...
     Assets: Figure, Table

[E2] Another Document · p. 4
     Evidence snippet...
```

The frontend should not need to understand LightRAG internals.

## Retrieval Access Policy

Recommended new boundary:

```text
RetrievalAccessPolicy
```

Responsibilities:

- resolve visible domains
- resolve allowed documents
- enforce shared-corpus or future tenant policy
- filter requested document IDs
- prevent retrieval engines from handling authorization

V1 behavior may be:

```text
All authenticated users can read all READY documents in visible shared domains.
Only admins can write.
```

But this must be documented as intentional.

## RAG Evaluation and Debugging

Future recommended additions:

- retrieval debug mode
- query route/mode logging
- evidence score logging
- LightRAG response timing
- provider latency/cost logging
- small evaluation dataset
- regression tests for known queries
- admin-only retrieval trace endpoint



---

# CODING_AGENT_GUIDE


# Coding Agent Guide

## Purpose

This guide tells coding agents and junior developers where to make changes safely in `context_engine`.

## First Files to Read

Read in this order:

```text
README.md
AGENTS.md
app/main.py
app/core/config.py
app/core/deps.py
app/api/routes/retrieve.py
app/services/retrieval_service.py
app/retrieval/strategies.py
app/retrieval/lightrag_remote_engine.py
app/retrieval/rich_navigation_engine.py
app/integrations/lightrag_remote_adapter.py
app/api/routes/admin.py
app/api/routes/lightrag_admin.py
app/storage/tables.py
docker-compose.yml
```

## Common Change Types

### Add a new API endpoint

Work in:

```text
app/api/routes/
app/api/schemas/ or equivalent schema module
app/services/
tests/api/
```

Rules:

- keep route thin
- create or reuse a service method
- add auth/admin dependency
- add tests
- update API docs

### Change retrieval behavior

Work in:

```text
app/services/retrieval_service.py
app/retrieval/
tests/test_retrieval_*.py
```

Rules:

- do not add duplicate query endpoints
- keep `/retrieve` canonical
- do not call LightRAG directly from route handlers
- preserve stable evidence response shape

### Add provider support

Work in:

```text
app/core/config.py
app/integrations/
app/services/lightrag_domain_service.py
docs/
.env.example
```

Rules:

- do not scatter provider-specific env logic
- prefer provider profiles or adapter config
- update docs and tests

### Change LightRAG domain lifecycle

Work in:

```text
app/api/routes/lightrag_admin.py
app/services/lightrag_domain_service.py
app/services/lightrag_domain_registry.py
app/core/config.py
docker-compose.yml
tests/test_lightrag_*.py
```

Rules:

- admin-only
- preserve domain registry consistency
- do not change storage paths casually
- test create/start/stop/delete/recreate flows

### Change document ingestion

Work in:

```text
app/api/routes/admin.py
app/services/document_service.py
app/workers/
app/storage/
tests/test_document_*.py
```

Rules:

- admin-only
- preserve original upload
- preserve status transitions
- define asset behavior clearly
- do not bypass background job tracking

### Change workspace tree

Work in:

```text
app/api/routes/workspace_tree.py
app/services/workspace_tree_service.py
app/storage/repositories/
tests/test_workspace_tree*.py
```

Rules:

- keep response lightweight
- filter by domain when requested
- avoid returning full document content by default

### Change configuration

Work in:

```text
app/core/config.py
.env.example
docker-compose.yml
docs/codebase-map/CONFIGURATION_AND_DEPLOYMENT.md
tests/test_config*.py
```

Rules:

- update `.env.example`
- add validation tests
- do not introduce undocumented env vars
- keep production guardrails

## Files to Be Careful With

High-risk files:

```text
app/core/config.py
app/storage/tables.py
alembic/versions/*
app/services/retrieval_service.py
app/integrations/lightrag_remote_adapter.py
docker-compose.yml
```

Why high-risk:

- can break deployment
- can break migrations
- can break retrieval
- can break LightRAG connectivity
- can change production security posture

## Safe Refactor Zones

Usually lower-risk:

```text
docs/
tests/fixtures/
small schema/response formatting helpers
clearly isolated evidence formatting utilities
README examples
```

Still run tests after any change.

## High-Risk Refactor Zones

Avoid casual changes in:

- auth/security
- document deletion/archive behavior
- storage paths
- migrations
- LightRAG container lifecycle
- retrieval routing
- query/evidence response contract
- provider API key handling

## Development Rules

1. Do not create a second semantic retrieval system inside `context_engine`.
2. Do not add new query APIs unless `/retrieve` cannot support the use case.
3. Do not let route handlers call LightRAG directly.
4. Do not let frontend-specific display logic leak deeply into retrieval engines.
5. Do not add env vars without updating `.env.example`.
6. Do not change storage paths without migration/backup notes.
7. Do not assume per-user private corpus exists unless an ADR and schema define it.
8. Do not use `latest` image tags for production LightRAG deployments.
9. Do not remove tests around retrieval, domain lifecycle, or ingestion without replacement.
10. Prefer incremental refactors over rewrites.

## Coding Agent Acceptance Criteria Template

For each task, include:

```md
## Goal

## Files Changed

## Behavior Before

## Behavior After

## Tests Added/Updated

## Manual Verification

## Risk Notes

## Rollback Notes
```

## Required Test Mindset

For retrieval changes, test:

- authenticated user can retrieve
- unauthenticated user cannot retrieve
- admin and regular user read behavior is as intended
- document filter respects selected domain
- unavailable LightRAG domain fails clearly
- local navigation retrieval still returns stable evidence shape
- asset enrichment does not break if no assets exist

For admin changes, test:

- regular user forbidden
- admin allowed
- job/status updated
- storage side effects are expected
- failure leaves recoverable state



---

# ARCHITECTURE_REVIEW


# Architecture Review

## 1. Executive Summary

`context_engine` is a backend-only, multi-user hybrid RAG service. The current architecture is generally strong and does not need a rewrite.

The codebase is moving toward a clear design:

```text
FastAPI API
  → service layer
  → PostgreSQL app state
  → Redis/RQ jobs
  → remote LightRAG semantic retrieval
  → local structured navigation retrieval
  → stable evidence API
```

The most important recommendations are:

1. Document shared-corpus access as intentional.
2. Resolve CLI/TUI support contradiction.
3. Pin LightRAG image versions in staging/production.
4. Add a small retrieval access policy.
5. Keep `/retrieve` as the canonical retrieval/evidence endpoint.

## 2. Major Strengths

### Remote LightRAG Boundary

The app treats LightRAG as an external runtime service instead of embedding LightRAG internals. This is a good low-entropy architecture choice.

### Admin-Only Writes

Document upload, reingest, delete, and domain lifecycle operations are admin-only concepts. This supports a simple multi-user model.

### Structured Document Navigation

The app supports local document structure: documents, pages, sections, chunks, and assets. This enables workspace tree and evidence panel features.

### Single Retrieval API

Moving toward `/retrieve` as the canonical evidence endpoint reduces API duplication.

### Production Guardrails

The config layer includes production safety posture such as rejecting weak secrets, wildcard origins, and SQLite in production.

## 3. Findings by Severity

## Critical

No confirmed critical issue from the reviewed architecture.

The shared-corpus access model becomes critical only if the intended product requires per-user private documents or tenant isolation.

## High

### [High] Shared-Corpus Access Model Must Be Explicit

**Problem:** The app appears to allow all authenticated users to read all ready documents in visible domains.

**Evidence:** Retrieval and document access flows currently treat user identity mainly as authentication, not row-level document filtering.

**Why it matters:** The app is multi-user. Future developers may assume per-user isolation exists when it does not.

**Recommendation:** Add an ADR documenting the V1 shared-corpus model.

**Effort:** Low  
**Risk:** Low  
**Priority:** P0

### [High] Production LightRAG Image Should Be Pinned

**Problem:** Using `latest` image tags risks deployment drift.

**Why it matters:** LightRAG behavior, APIs, environment settings, and storage assumptions can change across versions.

**Recommendation:** Reject `:latest` in staging/production config validation.

**Effort:** Low  
**Risk:** Low  
**Priority:** P1

## Medium

### [Medium] CLI/TUI Support Is Ambiguous

**Problem:** Project docs appear to conflict on whether CLI/TUI is supported.

**Why it matters:** Coding agents and junior developers will not know whether to preserve or ignore CLI-related code/tests.

**Recommendation:** Decide and document one posture.

Recommended posture:

```text
TUI is a developer-only backend API harness, not a product UI.
```

**Effort:** Low  
**Risk:** Low  
**Priority:** P1

### [Medium] Settings Class Is Becoming Too Broad

**Problem:** One settings class owns many unrelated concerns.

**Why it matters:** Future provider/domain/frontend config will make this harder to understand.

**Recommendation:** Keep one public `get_settings()` but split settings internally into named groups.

**Effort:** Medium  
**Risk:** Medium  
**Priority:** P2

### [Medium] Retrieval Authorization Should Be Centralized

**Problem:** Retrieval engines should not be responsible for access semantics, and currently user ID is not meaningful in engines.

**Why it matters:** Future per-domain or per-user access will be easier if policy is centralized.

**Recommendation:** Add `RetrievalAccessPolicy`.

**Effort:** Medium  
**Risk:** Medium  
**Priority:** P1/P2

### [Medium] Local Navigation Retrieval Is Brute-Force

**Problem:** Structured lookup may scan local document structures.

**Why it matters:** Fine for small-team use, but may degrade as corpus grows.

**Recommendation:** Keep simple for now. Add PostgreSQL full-text search only when performance evidence requires it.

**Effort:** Low now / Medium later  
**Risk:** Low  
**Priority:** P2

## Low

### [Low] CORS Should Remain Explicit in Production

Wildcard origins should stay rejected in production. Document expected frontend origins clearly.

### [Low] Query Text Privacy Default Is Good

Do not store raw query text by default unless explicitly enabled.

## Positive Findings

- Route structure is understandable.
- Service/repository split is useful.
- LightRAG HTTP boundary is a good design.
- Tests cover meaningful architecture areas.
- Background job approach is appropriate.
- `/retrieve` simplification is the right direction.

## 4. Architecture Fitness Scorecard

| Lens | Score | Notes |
|---|---:|---|
| Modularity | 4/5 | Good route/service/retrieval separation |
| Separation of concerns | 3.5/5 | Some concrete wiring could move into factories |
| Dependency direction | 3.5/5 | Mostly clean; improve policy/adapters |
| Data flow clarity | 4/5 | Main flows are traceable |
| Scalability | 3/5 | Appropriate for small internal deployment |
| Reliability | 3.5/5 | Good job/runtime model; improve provider failure handling |
| Security | 3.5/5 | Admin boundaries good; access model needs ADR |
| Testing | 4/5 | Meaningful tests exist |
| Observability | 3/5 | Needs tracing/metrics if production grows |
| Deployment readiness | 3.5/5 | Good Compose/migrations; pin images |
| Evolvability | 4/5 | Good foundation |
| Junior readability | 3.5/5 | Good layout; docs conflicts hurt clarity |

## 5. Final Recommendation

Do not rewrite the codebase.

Stabilize the current architecture by documenting decisions, clarifying access policy, keeping LightRAG as an adapter boundary, and preparing `/retrieve` as the frontend's stable evidence API.



---

# REFACTORING_ROADMAP


# Refactoring Roadmap

## Phase 0: Documentation and Safety Checks

### Task 0.1: Add Shared-Corpus ADR

**Goal:** Document current multi-user access behavior.

**Files likely affected:**

```text
docs/adr/ADR-001-shared-corpus-access-model.md
README.md
tests/
```

**Acceptance criteria:**

- ADR says all authenticated users can read all READY shared-corpus documents.
- ADR says only admins can write.
- ADR says no per-user private corpus exists in V1.
- Tests verify admin write boundary and regular-user read boundary.

**Risk:** Low

### Task 0.2: Resolve CLI/TUI Documentation Conflict

**Goal:** Clarify whether CLI/TUI is supported.

**Files likely affected:**

```text
README.md
AGENTS.md
docs/
tests/cli/
```

**Acceptance criteria:**

- README and AGENTS.md agree.
- If TUI retained, it is documented as developer-only harness.
- If deprecated, tests/docs are marked deprecated or removed.

**Risk:** Low

## Phase 1: Low-Risk Cleanup

### Task 1.1: Normalize Evidence Response Documentation

**Goal:** Make frontend contract explicit.

**Files likely affected:**

```text
docs/
app/api/schemas/
tests/test_retrieve*.py
```

**Acceptance criteria:**

- Evidence fields documented.
- Tests assert stable fields:
  - `reference_id`
  - `document_id`
  - `document_title`
  - `source_path`
  - `chunk_id`
  - `page_number`
  - `assets`

**Risk:** Low

### Task 1.2: Add Retrieval Smoke Tests

**Goal:** Prevent accidental `/retrieve` regression.

**Files likely affected:**

```text
tests/test_retrieve*.py
```

**Acceptance criteria:**

- test unauthenticated request rejected
- test regular user can retrieve from shared ready corpus
- test admin can retrieve
- test invalid domain fails clearly
- test document filter outside domain fails clearly

**Risk:** Low

## Phase 2: Configuration and Deployment Hardening

### Task 2.1: Reject LightRAG `latest` in Production

**Goal:** Prevent deployment drift.

**Files likely affected:**

```text
app/core/config.py
.env.example
tests/test_config*.py
docs/codebase-map/CONFIGURATION_AND_DEPLOYMENT.md
```

**Acceptance criteria:**

- production/staging config rejects `LIGHTRAG_IMAGE` ending in `:latest`
- local/dev may still use latest if desired
- docs explain how to pin and upgrade

**Risk:** Low

### Task 2.2: Group Settings by Concern

**Goal:** Reduce config entropy.

**Files likely affected:**

```text
app/core/config.py
tests/test_config*.py
```

**Acceptance criteria:**

- public `get_settings()` remains stable
- settings grouped by concern internally
- existing env vars still load
- production validation tests still pass

**Risk:** Medium

## Phase 3: Storage and Schema Clarity

### Task 3.1: Document Archive/Delete Behavior

**Goal:** Define what happens to uploaded files and assets.

**Files likely affected:**

```text
docs/adr/
app/services/document_service.py
tests/test_document_delete*.py
```

**Acceptance criteria:**

- archive behavior documented
- hard-delete behavior documented
- assets/images/tables behavior documented
- tests prove expected file/storage side effects

**Risk:** Medium

### Task 3.2: Add Domain Registry Consistency Check

**Goal:** Detect DB/manifest/domain storage mismatch.

**Files likely affected:**

```text
app/services/lightrag_domain_registry.py
app/api/routes/health.py
tests/test_lightrag_domain_registry*.py
```

**Acceptance criteria:**

- health/readiness can surface domain registry mismatch
- admin can identify orphaned domain storage
- no automatic destructive cleanup without explicit admin action

**Risk:** Medium

## Phase 4: API and Service Boundary Cleanup

### Task 4.1: Add RetrievalAccessPolicy

**Goal:** Centralize retrieval authorization and document scope resolution.

**Files likely affected:**

```text
app/services/retrieval_access_policy.py
app/services/retrieval_service.py
tests/test_retrieval_access_policy.py
```

**Acceptance criteria:**

- service resolves allowed document IDs before calling engines
- V1 shared-corpus behavior preserved
- future tenant/domain ACL logic has one place to go

**Risk:** Medium

### Task 4.2: Add Retrieval Service Factory

**Goal:** Avoid concrete dependency sprawl.

**Files likely affected:**

```text
app/api/deps.py or app/core/deps.py
app/services/retrieval_service.py
tests/
```

**Acceptance criteria:**

- route obtains RetrievalService through dependency/factory
- tests can inject mock engines/adapters
- behavior unchanged

**Risk:** Medium

## Phase 5: Observability and Testing

### Task 5.1: Add Retrieval Trace Metadata

**Goal:** Make retrieval debugging easier.

**Files likely affected:**

```text
app/services/retrieval_service.py
app/retrieval/
app/storage/repositories/log_repository.py
tests/
```

**Acceptance criteria:**

- retrieval logs mode/strategy/domain/duration
- raw query text remains disabled by default
- logs help debug LightRAG vs navigation behavior

**Risk:** Low/Medium

### Task 5.2: Add Provider/LightRAG Failure Tests

**Goal:** Ensure clean failure when LightRAG is down.

**Files likely affected:**

```text
tests/test_lightrag_remote_engine.py
tests/test_retrieve*.py
```

**Acceptance criteria:**

- timeout returns clear error
- unavailable domain returns clear error
- provider failure does not crash worker/API unexpectedly

**Risk:** Low

## Phase 6: Optional Architecture Improvements

### Task 6.1: PostgreSQL Full-Text Search for Navigation

**Goal:** Improve local navigation retrieval if corpus grows.

**Files likely affected:**

```text
app/storage/tables.py
alembic/versions/
app/retrieval/rich_navigation_engine.py
tests/
```

**Acceptance criteria:**

- only implemented if brute-force lookup becomes slow
- query results remain stable
- migration is reversible or safe
- performance improvement measured

**Risk:** Medium/High

### Task 6.2: Provider Profiles

**Goal:** Support OpenAI, OpenAI-compatible Bedrock, and other providers cleanly.

**Files likely affected:**

```text
app/core/config.py
app/services/lightrag_domain_service.py
app/integrations/providers/
docs/
tests/
```

**Acceptance criteria:**

- provider config centralized
- LightRAG domain env generation can select provider profile
- secrets are not leaked
- docs cover OpenAI and Bedrock-compatible setup

**Risk:** Medium



---

# ADRS_TO_WRITE


# Architecture Decision Records to Write

## ADR-001: Shared Corpus Access Model

### Decision Needed

Is the current V1 product intentionally a shared knowledge base where all authenticated users can read all READY documents in visible domains?

### Recommended Decision

Yes, for V1.

```text
All authenticated users can read READY documents in visible shared domains.
Only admins can upload, reingest, delete/archive, or manage LightRAG domains.
No per-user private corpus exists in V1.
```

### Why

This matches the small-team internal deployment model and keeps the system simple.

### Consequences

- Easier frontend integration.
- Easier retrieval logic.
- Must not market this as tenant-isolated.
- Future private scopes require schema and policy changes.

---

## ADR-002: LightRAG Runtime Boundary

### Decision Needed

Should `context_engine` embed LightRAG internals or keep LightRAG as a remote service?

### Recommended Decision

Keep LightRAG as a remote HTTP service.

### Why

This preserves a clean adapter boundary and avoids duplicating LightRAG internals.

### Consequences

- Backend depends on LightRAG API stability.
- Need domain health/status monitoring.
- Need pinned LightRAG versions in production.

---

## ADR-003: Canonical Retrieval API

### Decision Needed

Should the app expose multiple query endpoints or a single retrieval endpoint?

### Recommended Decision

Use `/retrieve` as the canonical retrieval/evidence API.

### Why

Reduces frontend confusion and backend duplication.

### Consequences

- All retrieval modes must fit under one request/response contract.
- Evidence shape must be stable.
- Old query endpoints should be removed or deprecated.

---

## ADR-004: Document Archive and Hard Delete Policy

### Decision Needed

What happens to uploaded files, extracted assets, local rows, and LightRAG indexed data when a document/domain is archived or deleted?

### Recommended Decision

Separate archive from hard delete.

```text
Archive:
  - hide from active retrieval
  - retain files/assets/metadata
  - allow recovery

Hard delete:
  - admin-only destructive operation
  - remove files/assets/local rows
  - remove or rebuild LightRAG index
  - write audit record
```

---

## ADR-005: LightRAG Domain Registry Source of Truth

### Decision Needed

Is the source of truth a manifest file, database table, or hybrid?

### Recommended Decision

Use one primary source of truth and document reconciliation behavior.

### Why

Manifest/DB drift can break domain listing, retrieval, and deployment lifecycle.

---

## ADR-006: Provider Configuration Strategy

### Decision Needed

How should OpenAI, OpenAI-compatible Bedrock, and future providers be configured?

### Recommended Decision

Use provider profiles.

Example:

```text
PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_BASE_URL=...

PROVIDER=bedrock_openai_compatible
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://...
```

### Consequences

- Less scattered provider logic.
- Easier domain env generation.
- Cleaner docs for junior developers.

---

## ADR-007: CLI/TUI Support Status

### Decision Needed

Is CLI/TUI supported, deprecated, or developer-only?

### Recommended Decision

Retain as developer-only backend API harness if it remains useful.

### Consequences

- README and AGENTS.md must agree.
- CLI tests should be kept only if harness is supported.
- Product frontend should not depend on TUI behavior.

---

## ADR-008: Observability Strategy

### Decision Needed

Should observability be native only, external tool-based, or hybrid?

### Recommended Decision

Start with native structured logs and query/job/domain health metadata. Consider Langfuse or similar only for LLM/retrieval traces, cost, and evaluation once the app has active usage.

### Consequences

- Avoids overbuilding observability too early.
- Leaves a clean path for Langfuse later.
