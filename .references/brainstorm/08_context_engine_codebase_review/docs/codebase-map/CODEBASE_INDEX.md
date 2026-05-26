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
