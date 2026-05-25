# 1. Architecture and Runtime Map

## 1.1 What This Codebase Does

`context_engine` is a backend-only multi-user hybrid RAG application. Its main purpose is to let authenticated users query indexed documents, while admin users manage ingestion and indexing.

The codebase includes:

- FastAPI backend application.
- SQLAlchemy persistence layer.
- User/auth/role model.
- Document upload, metadata, parsing, indexing, and retrieval services.
- Local semantic/navigation retrieval engines.
- Optional LightRAG remote retrieval and graph API proxy.
- Redis/RQ-based background indexing worker.
- Typer CLI named `ragcli` that calls backend API routes.
- Tests for API, CLI, retrieval routing, answer composition, LightRAG adapter behavior, and TUI/screen rendering support.

## 1.2 Runtime Architecture

```text
                         ┌─────────────────────────────┐
                         │      CLI / future UI         │
                         │  ragcli or frontend client   │
                         └──────────────┬──────────────┘
                                        │ HTTP JSON / multipart
                                        ▼
┌───────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                            │
│                                                                   │
│  app.main:create_app                                               │
│   ├── health router                                                │
│   ├── auth router                                                  │
│   ├── documents router                                             │
│   ├── admin router                                                 │
│   ├── query router                                                 │
│   ├── lightrag graph proxy router                                  │
│   └── jobs router                                                  │
│                                                                   │
│  Common dependencies:                                              │
│   ├── get_session()                                                │
│   ├── get_current_user()                                           │
│   └── require_admin()                                              │
└───────────────┬───────────────────────────────┬───────────────────┘
                │                               │
                ▼                               ▼
┌─────────────────────────────┐     ┌───────────────────────────────┐
│ SQLAlchemy database layer    │     │ File storage                   │
│ app.storage                  │     │ app.services.file_storage      │
│                              │     │ STORAGE_ROOT                   │
│ users                        │     └───────────────┬───────────────┘
│ documents                    │                     │
│ parsed_documents             │                     ▼
│ navigation_indexes           │     ┌───────────────────────────────┐
│ semantic_chunks              │     │ Indexing pipeline              │
│ jobs                         │     │ DocumentParser                 │
│ audit_logs                   │     │ NavigationIndexBuilder         │
│ query_logs                   │     │ SemanticIndexBuilder           │
└─────────────────────────────┘     └───────────────┬───────────────┘
                                                    │
                                                    ▼
                                      ┌───────────────────────────────┐
                                      │ Retrieval layer                │
                                      │ SemanticRetrievalEngine        │
                                      │ NavigationRetrievalEngine      │
                                      │ Hybrid merger/router           │
                                      │ Optional LightRAG remote engine│
                                      └───────────────────────────────┘

Optional background path:

Admin upload/index request
        │
        ▼
JobService.enqueue_index_document()
        │
        ├── if INDEX_JOBS_INLINE=true: run immediately in API process
        │
        └── if INDEX_JOBS_INLINE=false: enqueue RQ job in Redis queue `indexing`
                                      │
                                      ▼
                           app.workers.worker
                           app.workers.tasks.run_index_job()
```

## 1.3 Folder and Module Map

| Path | Purpose | Key Files | Notes |
|---|---|---|---|
| `app/` | Main backend application package. | `main.py` | FastAPI factory and router registration. |
| `app/api/` | API dependencies and routes. | `deps.py`, `routes/*.py` | Defines route surfaces and auth/admin guards. |
| `app/api/routes/` | HTTP route handlers. | `auth.py`, `documents.py`, `admin.py`, `query.py`, `jobs.py`, `lightrag.py`, `health.py` | Thin API layer over services/repositories. |
| `app/core/` | Cross-cutting core utilities. | `config.py`, `security.py`, `errors.py`, `logging.py` | Settings, JWT/password hashing, common errors/logging. |
| `app/domain/` | Domain models/enums. | `models.py` | App-level domain objects and statuses. |
| `app/indexing/` | Parsing and index construction. | `parsers.py`, `chunking.py`, `navigation_index_builder.py`, `semantic_index_builder.py` | Converts stored document files into parsed pages, nav tree, and semantic chunks. |
| `app/integrations/` | External/adapter layer. | `lightrag_remote_adapter.py`, `lightrag_adapter.py`, `lightrag_domains.py`, `pageindex_adapter.py` | LightRAG and page index integration boundaries. |
| `app/retrieval/` | Retrieval and answer composition. | `router.py`, `semantic_engine.py`, `navigation_engine.py`, `hybrid_merger.py`, `routing_policy.py`, `answer_composer.py` | Decides local/remote retrieval path and builds answer output. |
| `app/schemas/` | Pydantic request/response schemas. | `auth.py`, `documents.py`, `jobs.py`, `query.py` | API contracts. |
| `app/services/` | Application service layer. | `document_service.py`, `indexing_service.py`, `job_service.py`, `retrieval_service.py`, `file_storage.py` | Main business workflow orchestration. |
| `app/storage/` | Database setup and ORM tables. | `db.py`, `tables.py`, `repositories/*` | SQLAlchemy engine/session, table models, repository classes. |
| `app/workers/` | Background job worker. | `worker.py`, `tasks.py` | RQ worker and indexing task entrypoints. |
| `cli/` | Typer CLI. | `main.py`, `api_client.py`, `credentials.py` | API-calling CLI with auth/session persistence. |
| `docs/` | Documentation. | Multiple docs. | Should be treated as design/reference unless verified against code. |
| `scripts/` | Operational scripts. | `seed_admin.py` | Seeds admin account from environment settings. |
| `tests/` | Test suite. | `test_api.py`, `test_cli*.py`, etc. | Covers main API path, CLI/TUI support, LightRAG adapter, routing policy, answer composer. |
| `.env.example` | Environment template. | n/a | Useful but missing some optional LightRAG settings present in `Settings`. |
| `docker-compose.yml` | Local service orchestration. | n/a | API, PostgreSQL/pgvector, Redis, worker. |
| `Dockerfile` | Container build. | n/a | Used by compose/API/worker. |
| `pyproject.toml` | Python package metadata. | n/a | Dependencies and `ragcli` console script. |

## 1.4 Startup Flow

Primary entrypoint:

```text
app.main:create_app
```

Observed startup behavior:

1. `create_app()` loads settings using `get_settings()` from `app.core.config`.
2. It creates `FastAPI(title=settings.app_name, lifespan=lifespan)`.
3. It configures CORS using `settings.allowed_origins`.
4. It registers these routers:
   - `health.router`
   - `auth.router`
   - `documents.router`
   - `admin.router`
   - `query.router`
   - `lightrag.router`
   - `jobs.router`
5. The lifespan function runs:
   - `configure_logging()`
   - `create_db_and_tables()`
6. `create_db_and_tables()` imports table definitions and runs `Base.metadata.create_all(bind=engine)`.

Important implication: table creation is automatic at startup. This is simple for local/small deployments, but there is no explicit migration workflow in the reviewed files.

## 1.5 Deployment Shape

`docker-compose.yml` defines:

- `postgres` using `pgvector/pgvector:pg16`.
- `redis` using `redis:7-alpine`.
- `api` running `uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --reload`.
- `worker` running `python -m app.workers.worker`.

This is appropriate for local development and a small local-network deployment, but production deployment should carefully configure:

- `SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `ALLOWED_ORIGINS`
- `STORAGE_ROOT`
- `INDEX_JOBS_INLINE`
- optional LightRAG settings
