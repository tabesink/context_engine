# Codebase view: `easy-deploy-lightrag`

I used your attached software architecture reviewer + codebase documentation prompt as the rubric for this pass.  I inspected the public GitHub repo through the browser, but I could not complete a local clone in this environment, so this is a **repo-sampled architecture map**, not a committed `docs/codebase-map/` package.

## 1. Executive summary

This repo appears to be a **custom deployment wrapper around LightRAG** for running domain-specific knowledge bases through one entry point. The repository description says it deploys “LightRAG domain specific knowledge bases via a single entry-point,” and the root includes `src`, `client`, `cli`, `docs`, `scripts`, `tests`, `data`, `volume`, Docker files, and domain compose files. The language mix is primarily Python and TypeScript. ([GitHub][1])

The architecture is more serious than a simple LightRAG starter. It includes:

* A custom **FastAPI server wrapper**
* Cookie/JWT authentication
* SQLite-backed users, conversations, messages, audit logs, source tree snapshots, and rate limit events
* A domain discovery/proxy layer for LightRAG instances
* A React/Vite LightRAG WebUI
* Docker Compose infrastructure for PostgreSQL/pgvector, Redis, Neo4j, and a domain-specific LightRAG container
* A vendored/customized `src/lightrag` package

The biggest architectural issue is **operational clarity**: there are multiple entry points, multiple UI folders, multiple storage systems, and some mismatches between declared package scripts and inspected source layout. The system is promising, but it needs a durable `docs/codebase-map/` package before future coding agents make heavy changes.

## 2. Stack and runtime summary

| Area             | What I found                                                                              |
| ---------------- | ----------------------------------------------------------------------------------------- |
| Backend          | FastAPI + Uvicorn custom server under `src/server`                                        |
| RAG engine       | LightRAG under `src/lightrag`, copied into the Docker image                               |
| Auth             | Cookie-based JWT using PyJWT + bcrypt                                                     |
| Server DB        | SQLite at default `sqlite:///data/server/server.sqlite3`                                  |
| LightRAG storage | PostgreSQL/pgvector, Redis, Neo4j, mounted file volumes                                   |
| Frontend         | React/Vite WebUI under `src/lightrag_webui`; separate `client` folder also exists         |
| CLI              | `lightrag-cli = cli.main:main` via `pyproject.toml`                                       |
| Package manager  | Python `uv.lock`; WebUI has npm/bun scripts                                               |
| Deployment       | `Dockerfile.lightrag-local`, `docker-compose.domains.yml`                                 |
| Observability    | Basic health endpoint and request ID middleware seen; no full tracing/metrics layer found |
| Tests            | `tests/` folder exists; WebUI package includes test scripts                               |

The Python package metadata declares Python `>=3.10` and dependencies including FastAPI, Uvicorn, OpenAI, Ollama, Typer, Rich, bcrypt, PyJWT, pydantic, httpx, aiohttp, tenacity, nano-vectordb, and MCP tooling. It also declares scripts for `lightrag-cli`, `lightrag-mcp-server`, and `lightrag-backend`. ([GitHub][2])

## 3. Repository inventory

The root structure includes `.cursor`, `.notebooks`, `cli`, `client`, `data`, `docs`, `scripts`, `src`, `tests`, `volume`, `.env.example`, Docker files, compose files, `pyproject.toml`, and `uv.lock`. ([GitHub][1])

The main `src` folder contains four important areas:

```text
src/
  agent/
  lightrag/
  lightrag_webui/
  server/
```

The `server` folder is organized into domain-style modules:

```text
src/server/
  app/
  auth/
  config/
  context/
  conversations/
  lightrag/
  storage/
  users/
```

That is a good sign: auth, config, storage, conversations, LightRAG proxying, and user administration are separated into clear folders. ([GitHub][3])

The vendored/custom LightRAG package is substantial. It includes `api`, `kg`, `llm`, `tools`, `lightrag.py`, `operate.py`, `document_graph.py`, `structural_chunking.py`, `rerank.py`, `utils_graph.py`, and related modules. ([GitHub][4])

## 4. Current architecture map

```text
Browser / WebUI / client
  → FastAPI app in src/server/app/main.py
  → Auth middleware / cookie JWT / current-user dependencies
  → Routers:
      /api/v1/auth
      /api/v1/admin/users
      /api/conversations
      /api/lightrag
  → SQLite repositories:
      users
      conversations
      messages
      audit_log
      source_tree_snapshots
      rate_limit_events
  → LightRAG domain proxy layer
  → One or more LightRAG domain services
  → LightRAG storage:
      PostgreSQL / pgvector
      Redis
      Neo4j
      file volumes
```

The FastAPI app creates the application, adds CORS and request-ID middleware, exposes `/health`, bootstraps the admin user, discovers LightRAG domains, and includes auth, user, conversation, and LightRAG routers. ([GitHub][5])

The LightRAG domain service reads a domain manifest, checks domain health endpoints, and falls back to a default LightRAG base URL if no healthy manifest domains are found. ([GitHub][6])

## 5. RAG pipeline map

From the deployment and source layout, the intended RAG flow looks like this:

```text
Domain input documents
  → mounted input directory
  → LightRAG container
  → custom / vendored LightRAG package
  → parsing / chunking / indexing
  → vector + graph + KV/cache storage
  → retrieval through LightRAG APIs
  → FastAPI proxy/domain route
  → frontend/client response
```

The Docker Compose file defines backing services for PostgreSQL/pgvector, Redis, Neo4j, and a `lightrag_fatigue` service. That LightRAG service mounts domain-specific `rag_storage`, `inputs`, and `artifacts` directories, then starts LightRAG with a workspace named `fatigue`. ([GitHub][7])

This matches modern LightRAG concepts: LightRAG provides server/WebUI/API support and combines document indexing, knowledge graph exploration, and RAG querying. ([GitHub][8])

## 6. API map

### Auth API

```text
/api/v1/auth/login
/api/v1/auth/logout
/api/v1/auth/me
/api/v1/auth/change-password
```

The login route validates username/password, writes audit events for failed/successful login, creates a JWT, and sets an auth cookie. Logout clears the cookie. ([GitHub][9])

### Admin users API

```text
/api/v1/admin/users
/api/v1/admin/users/{user_id}
/api/v1/admin/users/{user_id}/reset-password
/api/v1/admin/users/pending-count
/api/v1/admin/users/{user_id}/mark-visited
```

The admin router supports listing, creating, updating, deleting, password reset, and onboarding/pending-status operations. It also includes protections against admins deleting themselves or changing their own role/write access. ([GitHub][10])

### Conversations API

```text
/api/conversations
/api/conversations/{conversation_id}
/api/conversations/{conversation_id}/messages
/api/conversations/{conversation_id}/source-tree
```

The conversations router supports conversation creation, message listing, source tree retrieval, and streaming message responses using `application/x-ndjson`. ([GitHub][11])

### LightRAG proxy API

```text
/api/lightrag/domains
/api/lightrag/entity-types
/api/lightrag/domains/{port}/graphs
/api/lightrag/domains/{port}/graph/label/popular
/api/lightrag/domains/{port}/graph/label/search
/api/lightrag/domains/{port}/graph/entity/exists
/api/lightrag/domains/{port}/graph/entity/edit
/api/lightrag/domains/{port}/graph/relation/edit
```

The LightRAG router separates read operations from write operations. Write operations require admin role or `can_write`; otherwise they return 403. ([GitHub][12])

## 7. Database and storage schema

The custom server uses SQLite, not just LightRAG storage. The schema is created in code and includes:

```text
users
audit_log
conversations
messages
source_tree_snapshots
rate_limit_events
```

The `users` table stores username, display name, password hash, role, write permission, activity status, onboarding status, and timestamps. The `conversations` and `messages` tables store user conversations and message metadata, including model, selected domain, and sources JSON. `audit_log` stores actor/action/resource metadata. ([GitHub][13])

The database layer currently supports only `sqlite:///` URLs. The connection helper creates the parent directory and runs schema initialization on connection. ([GitHub][13])

For LightRAG, the domain compose file uses PostgreSQL/pgvector, Redis, Neo4j, and file mounts. This means the repo has **two storage planes**:

```text
Control-plane app storage:
  SQLite users/conversations/audit/rate-limit/source-tree

RAG data-plane storage:
  PostgreSQL/pgvector
  Redis
  Neo4j
  mounted rag_storage/input/artifact directories
```

That distinction should be made very explicit in documentation.

## 8. Deployment map

The domain compose file starts:

```text
postgres
redis
neo4j
lightrag_fatigue
```

It uses health checks for PostgreSQL, Redis, and Neo4j, and the LightRAG domain service depends on those services being healthy. Docker Compose supports dependency ordering through `depends_on`, and health-based service conditions are the right pattern for this kind of dependency chain. ([GitHub][7])

The custom Dockerfile uses `ghcr.io/hkuds/lightrag:latest`, installs extra dependencies such as `docling` and `pyuca`, installs system libraries, and copies the repo’s `src/lightrag` into `/app/lightrag`. ([GitHub][14])

Important deployment concern: the compose file exposes the LightRAG domain container on `127.0.0.1:9622`, while the server settings default to LightRAG base URL `http://127.0.0.1:9621`. That may be intentional for a default domain, but it should be documented because it can confuse future agents debugging “server cannot reach LightRAG” issues. ([GitHub][15])

## 9. Findings by severity

### Critical — Development defaults are unsafe if used in production

**Problem:** The default settings include `admin/admin123`, `local-development-change-me` as the JWT secret, and non-secure cookies by default.

**Evidence:** `Settings` defines default admin username/password, JWT secret, and cookie security defaults. ([GitHub][15]) The auth layer bootstraps the admin user from those settings and signs JWTs using the configured secret. ([GitHub][16])

**Why it matters:** If these defaults leak into a deployed environment, the system is exposed to admin compromise.

**Recommendation:** Fail startup in production unless `BACKEND_ADMIN_PASSWORD`, `BACKEND_JWT_SECRET`, and secure cookie settings are explicitly configured.

**Priority:** P0.

---

### High — Entrypoint/package naming appears inconsistent

**Problem:** `pyproject.toml` declares `lightrag-backend = backend.main:main`, but the inspected FastAPI app lives under `src/server/app/main.py`.

**Evidence:** Script definitions and package mappings are in `pyproject.toml`; the actual app factory and Uvicorn main function are under `src/server/app/main.py`. ([GitHub][2])

**Why it matters:** Coding agents may modify the wrong server entry point or create duplicate backend paths.

**Recommendation:** Decide whether the backend package is `backend` or `server`, then align scripts, imports, docs, and deployment commands.

**Priority:** P1.

---

### High — Storage strategy needs explicit control-plane vs RAG-plane documentation

**Problem:** SQLite handles users/conversations/audit logs while LightRAG uses PostgreSQL, Redis, Neo4j, and file volumes. This is a reasonable split, but it is not obvious from the top-level structure.

**Evidence:** SQLite schema is defined in `src/server/storage/db.py`; LightRAG services and volumes are defined in `docker-compose.domains.yml`. ([GitHub][13])

**Why it matters:** Future changes to backups, migrations, tenant isolation, retention, or reset scripts could accidentally wipe business-critical data.

**Recommendation:** Create `docs/codebase-map/DATABASE_AND_STORAGE_SCHEMA.md` with “safe to delete,” “persistent,” “backup required,” and “generated/cache” classifications.

**Priority:** P1.

---

### High — Docker image uses an unpinned upstream `latest` base

**Problem:** `Dockerfile.lightrag-local` builds from `ghcr.io/hkuds/lightrag:latest`.

**Evidence:** The Dockerfile starts from the `latest` LightRAG image and then overlays custom source files. ([GitHub][14])

**Why it matters:** Future builds may change behavior without a code change in this repo.

**Recommendation:** Pin the upstream image by version or digest, and document the upgrade process.

**Priority:** P1.

---

### Medium — Domain fallback can mask broken deployment

**Problem:** If no healthy manifest domains are found, the domain service falls back to a default domain.

**Evidence:** Domain discovery reads the manifest, checks health, and falls back to the configured default LightRAG base URL. ([GitHub][6])

**Why it matters:** In development this is convenient; in production it could hide that domain-specific services failed to start.

**Recommendation:** Add an environment flag such as `BACKEND_ALLOW_DOMAIN_FALLBACK=false` for production.

**Priority:** P2.

---

### Medium — UI ownership is unclear

**Problem:** There is a `client` folder and also a `src/lightrag_webui` folder.

**Evidence:** The root has `client`; `src/lightrag_webui` is a React/Vite WebUI with its own package scripts and dependencies. ([GitHub][1])

**Why it matters:** Future agents may patch the wrong UI.

**Recommendation:** Add a short `docs/codebase-map/UI_OWNERSHIP.md` or include this in `CODEBASE_INDEX.md`.

**Priority:** P2.

---

### Positive — Server module boundaries are understandable

The `src/server` structure separates app bootstrapping, auth, config, conversations, LightRAG proxying, storage, and users. This is good for junior-developer readability and future coding-agent work. ([GitHub][3])

### Positive — Admin write boundary exists for graph edits

The LightRAG proxy routes require admin or `can_write` for graph entity/relation edits. That is a useful early authorization boundary. ([GitHub][12])

## 10. Architecture scorecard

| Lens                   | Score | Notes                                                                 |
| ---------------------- | ----: | --------------------------------------------------------------------- |
| Modularity             |   4/5 | Server folders are clear                                              |
| Separation of concerns | 3.5/5 | Good server split; UI/entrypoint ownership unclear                    |
| Dependency direction   |   3/5 | Needs deeper local inspection                                         |
| Data flow clarity      |   3/5 | Understandable but undocumented                                       |
| Storage clarity        | 2.5/5 | Two storage planes need explicit docs                                 |
| Security               | 2.5/5 | Good bcrypt/JWT structure, unsafe defaults need production guardrails |
| Observability          |   2/5 | Basic health/request ID seen; no full metrics/tracing found           |
| Deployment readiness   |   3/5 | Compose is substantial, but server/domain topology needs alignment    |
| Testing                | 2.5/5 | Test folders/scripts exist; coverage not verified                     |
| Junior readability     | 3.5/5 | Promising, needs codebase map                                         |
| Coding-agent readiness | 2.5/5 | Needs generated docs and “safe/risky files” guide                     |

## 11. Recommended `docs/codebase-map/` package

Your prompt asks for these files, and this repo is ready for them. I did not find this exact folder in the sampled top-level docs listing; existing docs include `DESIGN.md`, `database-schema.txt`, `prd.md`, `tech-stack.md`, `test-strategy.md`, and related planning docs. ([GitHub][17])

Create:

```text
docs/codebase-map/
  README.md
  CODEBASE_INDEX.md
  ARCHITECTURE.md
  PRD.md
  API_MAP.md
  DATABASE_AND_STORAGE_SCHEMA.md
  CONFIGURATION_AND_DEPLOYMENT.md
  RAG_PIPELINE.md
  CODING_AGENT_GUIDE.md
  ARCHITECTURE_REVIEW.md
  REFACTORING_ROADMAP.md
  ADRS_TO_WRITE.md
```

The most important first three are:

```text
CODEBASE_INDEX.md
DATABASE_AND_STORAGE_SCHEMA.md
CONFIGURATION_AND_DEPLOYMENT.md
```

Those will prevent most future coding-agent mistakes.

## 12. Prioritized improvement plan

### Phase 0 — Documentation safety pass

Create `docs/codebase-map/` and document current repo structure, entry points, storage, deployment, and API routes.

Acceptance criteria: a new developer can answer “where do I add an endpoint?”, “where does user data live?”, and “what data must be backed up?”

### Phase 1 — Production configuration guardrails

Add startup validation for production mode:

```text
BACKEND_JWT_SECRET must be changed
BACKEND_ADMIN_PASSWORD must be changed
BACKEND_AUTH_COOKIE_SECURE=true
CORS origins must be explicit
domain fallback must be explicit
```

Acceptance criteria: unsafe defaults cannot boot in production.

### Phase 2 — Entrypoint cleanup

Align `pyproject.toml`, package names, Docker commands, README commands, and actual app entry points.

Acceptance criteria: there is one documented command for local server startup and one documented command for production startup.

### Phase 3 — Storage classification

Document every persistent directory/table/backend:

```text
SQLite server DB
Postgres/pgvector
Redis
Neo4j
rag_storage
inputs
artifacts
```

Acceptance criteria: docs say what is safe to delete, what is cache, what is source input, and what needs backup.

### Phase 4 — Observability

Add structured logs for:

```text
request_id
user_id
domain_id
conversation_id
LightRAG call latency
provider/model
token/cost estimate if available
errors
```

Acceptance criteria: an admin/dev can trace one user question from API request to LightRAG call to response.

## 13. ADRs to write

```text
ADR-001: Backend package naming and entrypoint strategy
ADR-002: Control-plane SQLite vs RAG-plane storage split
ADR-003: LightRAG domain deployment model
ADR-004: Domain manifest and fallback behavior
ADR-005: Authentication and authorization model
ADR-006: Admin-only write boundary for graph operations
ADR-007: Persistent data backup and restore strategy
ADR-008: Frontend ownership: client vs lightrag_webui
ADR-009: Observability and audit logging strategy
ADR-010: Upstream LightRAG version pinning and customization policy
```

## 14. Research consulted

| Source                               | Why consulted                                           | Takeaway                                                                                                                                                                            |
| ------------------------------------ | ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Official LightRAG repo/docs          | Confirm current LightRAG server/WebUI/API concepts      | LightRAG supports WebUI/API workflows for indexing, graph exploration, and RAG querying. ([GitHub][8])                                                                              |
| FastAPI security docs                | Validate auth/security expectations                     | FastAPI provides security tools, but password hashing, JWT handling, and secure config remain application responsibilities. ([FastAPI][18])                                         |
| Docker Compose docs                  | Validate compose dependency/health-check interpretation | Compose supports service definitions, volumes, networks, and dependency ordering; health checks are appropriate for DB/Redis/Neo4j startup sequencing. ([Docker Documentation][19]) |
| Neo4j LightRAG engineering reference | Understand LightRAG graph/vector pipeline framing       | LightRAG-style pipelines combine document chunking, entity/relation extraction, graph storage, vector search, and hybrid retrieval. ([Graph Database & Analytics][20])              |

## Bottom line

This repo has a good foundation for a **domain-specific LightRAG deployment platform**, not just a quick demo. The main next step is not rewriting code. It is creating the codebase knowledge base your prompt describes, then hardening production defaults, entrypoint consistency, storage documentation, and observability.

[1]: https://github.com/tabesink/easy-deploy-lightrag.git "GitHub - tabesink/easy-deploy-lightrag: Deploy LightRAG domain specific knowledge bases via a single entry-point · GitHub"
[2]: https://github.com/tabesink/easy-deploy-lightrag/blob/main/pyproject.toml "easy-deploy-lightrag/pyproject.toml at main · tabesink/easy-deploy-lightrag · GitHub"
[3]: https://github.com/tabesink/easy-deploy-lightrag/tree/main/src/server "easy-deploy-lightrag/src/server at main · tabesink/easy-deploy-lightrag · GitHub"
[4]: https://github.com/tabesink/easy-deploy-lightrag/tree/main/src/lightrag "easy-deploy-lightrag/src/lightrag at main · tabesink/easy-deploy-lightrag · GitHub"
[5]: https://github.com/tabesink/easy-deploy-lightrag/blob/main/src/server/app/main.py "easy-deploy-lightrag/src/server/app/main.py at main · tabesink/easy-deploy-lightrag · GitHub"
[6]: https://github.com/tabesink/easy-deploy-lightrag/blob/main/src/server/lightrag/domain_service.py "easy-deploy-lightrag/src/server/lightrag/domain_service.py at main · tabesink/easy-deploy-lightrag · GitHub"
[7]: https://github.com/tabesink/easy-deploy-lightrag/blob/main/docker-compose.domains.yml "easy-deploy-lightrag/docker-compose.domains.yml at main · tabesink/easy-deploy-lightrag · GitHub"
[8]: https://github.com/hkuds/lightrag?utm_source=chatgpt.com "LightRAG: Simple and Fast Retrieval-Augmented Generation"
[9]: https://github.com/tabesink/easy-deploy-lightrag/blob/main/src/server/auth/router.py "easy-deploy-lightrag/src/server/auth/router.py at main · tabesink/easy-deploy-lightrag · GitHub"
[10]: https://github.com/tabesink/easy-deploy-lightrag/blob/main/src/server/users/router_admin.py "easy-deploy-lightrag/src/server/users/router_admin.py at main · tabesink/easy-deploy-lightrag · GitHub"
[11]: https://github.com/tabesink/easy-deploy-lightrag/blob/main/src/server/conversations/router.py "easy-deploy-lightrag/src/server/conversations/router.py at main · tabesink/easy-deploy-lightrag · GitHub"
[12]: https://github.com/tabesink/easy-deploy-lightrag/blob/main/src/server/lightrag/router.py "easy-deploy-lightrag/src/server/lightrag/router.py at main · tabesink/easy-deploy-lightrag · GitHub"
[13]: https://github.com/tabesink/easy-deploy-lightrag/blob/main/src/server/storage/db.py "easy-deploy-lightrag/src/server/storage/db.py at main · tabesink/easy-deploy-lightrag · GitHub"
[14]: https://github.com/tabesink/easy-deploy-lightrag/blob/main/Dockerfile.lightrag-local "easy-deploy-lightrag/Dockerfile.lightrag-local at main · tabesink/easy-deploy-lightrag · GitHub"
[15]: https://github.com/tabesink/easy-deploy-lightrag/blob/main/src/server/config/settings.py "easy-deploy-lightrag/src/server/config/settings.py at main · tabesink/easy-deploy-lightrag · GitHub"
[16]: https://github.com/tabesink/easy-deploy-lightrag/blob/main/src/server/auth/security.py "easy-deploy-lightrag/src/server/auth/security.py at main · tabesink/easy-deploy-lightrag · GitHub"
[17]: https://github.com/tabesink/easy-deploy-lightrag/tree/main/docs "easy-deploy-lightrag/docs at main · tabesink/easy-deploy-lightrag · GitHub"
[18]: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/?utm_source=chatgpt.com "OAuth2 with Password (and hashing), Bearer with JWT ..."
[19]: https://docs.docker.com/compose/how-tos/startup-order/?utm_source=chatgpt.com "Control startup and shutdown order in Compose"
[20]: https://neo4j.com/blog/developer/under-the-covers-with-lightrag-extraction/?utm_source=chatgpt.com "Under the Covers With LightRAG: Extraction"
