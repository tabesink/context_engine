# Context Engine LightRAG Deployment, Storage, Environment, and Concurrency Review

Repository reviewed: `https://github.com/tabesink/context_engine.git`

Purpose of this document: explain how LightRAG is currently wired into the codebase, where documents and embeddings are stored, what environment values matter, whether 5–10 users can retrieve concurrently, whether admin indexing can happen during retrieval, and which implementation option should be selected for a coding agent.

_Last verified against the codebase: May 2026. For a living implementation summary see `docs/implementation-status.md`._

This report is written for two audiences:

1. **You, as the product/architecture decision maker.** You need to choose a deployment direction.
2. **A junior developer or coding agent.** They need enough concrete file-path evidence to implement the chosen direction without guessing.

---

## 01 Executive Summary

### The most important finding

The current codebase has **two different LightRAG-related concepts**, and they should not be confused.

#### Concept A — Local backend semantic indexing, using a class named `LightRAGAdapter`

This is implemented today.

The backend has a local adapter at:

```text
app/integrations/lightrag_adapter.py
```

Despite the name, this is **not a deployed external LightRAG database**. It creates deterministic local hash-based embeddings for testing and local development. These embeddings are stored inside the backend database table:

```text
semantic_chunks.embedding
```

That means the backend currently has a local RAG-like semantic retrieval path that does not require a LightRAG server.

#### Concept B — Remote LightRAG server integration over HTTP

This is implemented for retrieval, upload forwarding, graph proxy, and domain-aware routing. Remaining gaps are operational hardening (status polling, ingest locking), not the core HTTP client.

The backend has a remote LightRAG HTTP client at:

```text
app/integrations/lightrag_remote_adapter.py
```

This adapter can:

- retrieve from a remote LightRAG server;
- upload a document to a remote LightRAG server;
- ask the remote server for document indexing status;
- proxy graph-related endpoints.

However, the root `docker-compose.yml` does **not** deploy a LightRAG service. The app expects an external LightRAG server if `LIGHTRAG_ENABLED=true`.

#### Concept C — LightRAG domain deployment manager

There is a separate package:

```text
app/lightrag_deploy/
```

It generates per-domain LightRAG containers, environment files, and Docker Compose YAML under paths like:

```text
.data/lightrag/domains/<domain_id>/inputs
.data/lightrag/domains/<domain_id>/rag_storage
.data/lightrag/domains/<domain_id>/artifacts
.data/lightrag/domains/<domain_id>/logs
```

This package **is wired into the FastAPI app** when `LIGHTRAG_DEPLOY_ENABLED=true`:

```text
app/api/routes/lightrag_admin.py   # admin lifecycle + GET /lightrag/domains
app/main.py                        # includes lightrag_admin.router
app/core/config.py                 # lightrag_deploy_* settings
```

Graph proxy routes remain in `app/api/routes/lightrag.py`. Mutating domain APIs are gated by `LIGHTRAG_DEPLOY_ENABLED`; read-only `GET /lightrag/domains` is available to authenticated users for domain selection.

**Remaining gaps for Concept C:** no background status poller from `track_id` to local `READY`; no per-domain ingestion lock; root `docker-compose.yml` still does not start LightRAG containers (domains use generated `.data/lightrag/docker-compose.lightrag-domains.yml`).

---

## 02 Current LightRAG Deployment Model

### 02.1 What the root Docker Compose deploys today

The root Docker Compose file deploys these services:

```text
postgres
redis
api
worker
```

It does **not** deploy a LightRAG container.

Evidence:

```text
docker-compose.yml
```

Observed services:

```text
postgres:
  image: pgvector/pgvector:pg16

redis:
  image: redis:7-alpine

api:
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

worker:
  command: python -m app.workers.worker
```

### 02.2 What this means in plain English

When you run the current default Docker Compose deployment, you get:

1. A backend API.
2. A backend worker.
3. A backend PostgreSQL database.
4. A backend Redis instance.

You do **not** automatically get LightRAG.

So if `LIGHTRAG_ENABLED=true`, the backend expects something else to already be running at:

```text
LIGHTRAG_BASE_URL=http://localhost:9621
```

or at a domain-specific URL defined in a manifest file.

### 02.3 Is there one LightRAG instance or multiple domain instances?

Current answer:

```text
Implemented in current runtime:
- One configured remote LightRAG base URL by default.
- Optional domain routing through a manifest file (LIGHTRAG_DOMAIN_MANIFEST / LIGHTRAG_DOMAINS_MANIFEST).
- Per-domain deployment generation and admin lifecycle under app/lightrag_deploy/ + lightrag_admin routes.
- CLI/TUI screens for domain management.

Not deployed by default:
- LightRAG containers in root docker-compose.yml (use generated domain compose or external service).
```

### 02.4 How remote LightRAG domains are resolved

The file:

```text
app/integrations/lightrag_domains.py
```

contains the domain-resolution logic.

The backend tries to resolve a requested LightRAG domain like this:

1. If a domain manifest exists, find the matching domain entry.
2. Use that domain entry's `base_url` and `api_key`.
3. If no manifest exists, fall back to the global settings:

```text
LIGHTRAG_BASE_URL
LIGHTRAG_API_KEY
LIGHTRAG_DOMAIN
```

This means the code already has a clean idea: **domain name maps to LightRAG base URL**. Admin create/up/down/recreate and manifest generation are available when `LIGHTRAG_DEPLOY_ENABLED=true`. The missing part is hardening (status refresh, ingest lock, optional per-upload engine selection).

### 02.5 Is LightRAG deployed per user?

No evidence shows per-user LightRAG deployment.

The current model is domain-oriented, not user-oriented.

Recommended interpretation:

```text
LightRAG domain = knowledge corpus / documentation collection.
User = authenticated person allowed to query one or more domains.
```

For your 5–10 user local-network app, this is the correct conceptual model. Do not deploy LightRAG per user unless there is a strict data-isolation requirement.

---

## 03 Current LightRAG Storage Model

## 03.1 Local backend document storage path

When the backend handles a document upload, it saves the uploaded file through:

```text
app/services/file_storage.py
```

The storage root comes from:

```text
STORAGE_ROOT=.data/uploads
```

The file is saved with a UUID filename under that root.

Plain-English flow:

```text
Admin uploads file
↓
FastAPI receives UploadFile
↓
DocumentService.upload() runs
↓
FileStorage.save_upload() writes the file into STORAGE_ROOT
↓
Document row is created in PostgreSQL
↓
Indexing job is queued or run inline
```

### 03.2 Local backend parsed text storage

The local backend parser/indexer stores parsed document output in backend PostgreSQL tables:

```text
parsed_documents
navigation_indexes
semantic_chunks
```

The table definitions are in:

```text
app/storage/tables.py
```

The repository methods are in:

```text
app/storage/repositories/documents.py
```

Relevant repository methods:

```text
save_parsed()
save_navigation_index()
replace_semantic_chunks()
list_semantic_chunks()
```

### 03.3 Local backend embedding storage

For the local backend RAG path, embeddings are stored in:

```text
semantic_chunks.embedding
```

The embedding is stored as JSON / JSONB list-of-floats, not as a pgvector column.

Important implication:

```text
The current local semantic retrieval path is simple but not optimized for large vector search.
```

For 5–10 users and modest document size, this may be acceptable during development. For larger corpora, it should eventually move to pgvector or to the real LightRAG backend.

### 03.4 Remote LightRAG upload storage

When `LIGHTRAG_ENABLED=true`, `DocumentService.upload()` branches into:

```text
DocumentService._upload_remote()
```

That method still saves a local copy of the uploaded file into:

```text
STORAGE_ROOT=.data/uploads
```

Then it calls:

```text
LightRAGRemoteAdapter.for_domain().upload_document(...)
```

which posts the file to the remote LightRAG server endpoint:

```text
POST /documents/upload
```

The backend stores remote LightRAG metadata on the local `documents` row:

```text
metadata = {
  "lightrag": {
    "enabled": true,
    "domain": settings.lightrag_domain,
    "document_id": remote.get("document_id"),
    "track_id": remote.get("track_id"),
    "status": remote.get("status"),
    "message": remote.get("message")
  }
}
```

### 03.5 Where remote LightRAG embeddings are stored

The backend code does not directly store real LightRAG embeddings.

For remote LightRAG, embeddings are stored by the remote LightRAG service, not by the backend app.

The deployment manager suggests the intended per-domain storage root is:

```text
.data/lightrag/domains/<domain_id>/rag_storage
```

The generated LightRAG domain environment file sets:

```text
WORKSPACE=<domain_id>
INPUT_DIR=/app/data/inputs
WORKING_DIR=/app/data/rag_storage
LOG_DIR=/app/data/logs
```

And the generated Compose service mounts host directories into the container:

```text
.data/lightrag/domains/<domain_id>/inputs     -> /app/data/inputs
.data/lightrag/domains/<domain_id>/rag_storage -> /app/data/rag_storage
.data/lightrag/domains/<domain_id>/logs       -> /app/data/logs
```

Therefore, the best current interpretation is:

```text
Remote LightRAG embeddings and graph state should live inside the per-domain rag_storage folder, if using the generated domain deployment model.
```

The LightRAG service is not in root Docker Compose; domains run via generated compose or an external server. Operators must start domain containers and verify storage layout at runtime.

### 03.6 Storage summary table

| Data | Current Local Backend Mode | Remote LightRAG Mode |
|---|---|---|
| Raw uploaded file | `.data/uploads/<uuid>.<ext>` | Local copy in `.data/uploads`, plus remote upload to LightRAG |
| Document metadata | `documents` table | `documents` table, with `meta.lightrag` fields |
| Parsed text | `parsed_documents` table | Stored by remote LightRAG; not directly visible to backend |
| Navigation tree | `navigation_indexes` table | Not confirmed in backend; LightRAG graph endpoints are proxied |
| Local embeddings | `semantic_chunks.embedding` JSON/JSONB | Not used |
| Real LightRAG embeddings | Not applicable | Expected under domain `rag_storage`, but exact internal files controlled by LightRAG |
| Graph data | Not real LightRAG graph | Expected under domain `rag_storage`, and graph endpoints proxied via HTTP |
| Query logs | `query_logs` table | `query_logs` table still used by backend retrieval service |

---

## 04 Environment Variables Required for LightRAG

The current `.env.example` documents both runtime integration and domain deployment control. **Code defaults** in `app/core/config.py` use `LIGHTRAG_ENABLED=false` and `LIGHTRAG_DEPLOY_ENABLED=false`; the example file sets both to `true` for local LightRAG development.

Runtime integration (excerpt):

```text
LIGHTRAG_ENABLED=true
LIGHTRAG_BASE_URL=http://localhost:9621
LIGHTRAG_API_KEY=
LIGHTRAG_DOMAIN=default
LIGHTRAG_DOMAIN_MANIFEST=.data/lightrag/domains.json
LIGHTRAG_TIMEOUT_SECONDS=10
```

Domain deployment control (excerpt):

```text
LIGHTRAG_DEPLOY_ENABLED=true
LIGHTRAG_DEPLOY_ROOT=.data/lightrag
LIGHTRAG_DOMAINS_ROOT=.data/lightrag/domains
LIGHTRAG_DOMAINS_MANIFEST=.data/lightrag/domains.json
LIGHTRAG_COMPOSE_FILE=.data/lightrag/docker-compose.lightrag-domains.yml
LIGHTRAG_DOCKER_TIMEOUT_SECONDS=120
```

See `.env.example` for the full list including optional Postgres/Redis/Neo4j overrides for LightRAG.

### 04.1 Required env table

| Env Variable | Required? | Used By | Purpose | Code default (`Settings`) | Recommended local value |
|---|---:|---|---|---|---|
| `LIGHTRAG_ENABLED` | Yes, if using remote LightRAG | Upload, retrieval routing, graph proxy | Enables remote LightRAG path | `false` | `true` only after a domain container or external server is running |
| `LIGHTRAG_BASE_URL` | Yes, for single-domain remote mode | `LightRAGRemoteAdapter` | Remote LightRAG API URL | `http://localhost:9621` | Host URL or Docker network service URL |
| `LIGHTRAG_API_KEY` | If remote LightRAG requires auth | `LightRAGRemoteAdapter` | Bearer token | empty | Strong token if auth enabled |
| `LIGHTRAG_DOMAIN` | Yes | Domain resolver, upload metadata | Default domain name | `default` | e.g. `manuals`, `catalogs` |
| `LIGHTRAG_DOMAIN_MANIFEST` | For multiple domains | `resolve_lightrag_domain()` | JSON manifest of domain → base URL | `.data/lightrag/domains.json` | Same path as generated manifest |
| `LIGHTRAG_TIMEOUT_SECONDS` | Yes | HTTP client timeout | Request timeout | `10` | `10–30` depending on hardware/LLM |
| `LIGHTRAG_DEPLOY_ENABLED` | For admin domain CRUD/up/down | `lightrag_admin` routes | Gates mutating deploy APIs | `false` | `true` when operators manage domains via API/TUI |
| `LIGHTRAG_DEPLOY_ROOT` | When deploy enabled | `LightRAGDomainService` | Root for generated artifacts | `.data/lightrag` | Persistent mounted path |
| `LIGHTRAG_DOMAINS_MANIFEST` | When deploy enabled | Manifest read/write | Same file as `LIGHTRAG_DOMAIN_MANIFEST` typically | `.data/lightrag/domains.json` | Keep in sync with resolver |
| `DATABASE_URL` | Yes | SQLAlchemy | Backend DB | `sqlite:///./.data/context_engine.db` | Postgres URL when using root compose |
| `REDIS_URL` | Yes, if background jobs | RQ / worker | Indexing queue | `redis://localhost:6379/0` | Redis service URL in Docker |
| `INDEX_JOBS_INLINE` | Important | `JobService` | Inline vs worker indexing | `false` | Keep `false` for concurrency |
| `STORAGE_ROOT` | Yes | `FileStorage` | Raw upload storage | `.data/uploads` | Persistent path |
| `SECRET_KEY` | Yes | Auth | JWT signing | dev placeholder | Strong random secret |
| `SEED_ADMIN_PASSWORD` | Yes for setup | Seed script | Initial admin login | example | Strong password |

### 04.2 Deployment settings (implemented)

`app/lightrag_deploy/settings.py` maps from `app/core/config.py` via `LightRAGDeploySettings.from_app_settings()`. All of the following are defined in both `Settings` and `.env.example`:

```text
LIGHTRAG_DEPLOY_ENABLED
LIGHTRAG_DEPLOY_ROOT
LIGHTRAG_DOMAINS_ROOT
LIGHTRAG_DOMAINS_MANIFEST
LIGHTRAG_COMPOSE_FILE
LIGHTRAG_DELETED_ROOT
LIGHTRAG_DEFAULT_PORT_START
LIGHTRAG_DEFAULT_CONTAINER_PORT
LIGHTRAG_DOCKER_NETWORK
LIGHTRAG_DOMAIN_ENV_FILENAME
LIGHTRAG_IMAGE
LIGHTRAG_DOCKER_EXECUTION_MODE
LIGHTRAG_DOCKER_COMPOSE_BIN
LIGHTRAG_DOCKER_TIMEOUT_SECONDS
```

Optional LightRAG external storage overrides (only if you configure LightRAG to use them): `LIGHTRAG_POSTGRES_URL`, `LIGHTRAG_REDIS_URL`, `LIGHTRAG_NEO4J_*`.

Tests: `tests/test_lightrag_deploy_settings.py`.

### 04.3 Optional Postgres/Redis for LightRAG internals

Only add or wire separate Postgres/Redis for LightRAG if the selected implementation explicitly configures LightRAG to use those external stores (Option 3+). Option 1 keeps LightRAG state file-based under `.data/lightrag/domains/<domain_id>/rag_storage`.

---

## 05 Concurrent Retrieval Assessment

## 05.1 Can 5–10 users retrieve context concurrently?

### Local backend retrieval mode

Current local retrieval reads semantic chunks from the backend database and scores them in Python.

The retrieval route is:

```text
POST /query/retrieve
POST /query/answer
POST /query
```

The route calls:

```text
RetrievalService(session).retrieve(...)
RetrievalService(session).answer(...)
```

The local retrieval engine reads from:

```text
semantic_chunks
```

and uses the local deterministic embedding adapter.

Assessment:

```text
Safe for 5–10 users:
- Likely acceptable for small/medium document sets.
- Retrieval is read-heavy.
- Background indexing can run in the worker if INDEX_JOBS_INLINE=false.

Risky for 5–10 users:
- Python-side scoring over many JSON embeddings will not scale well.
- No pgvector index is used for local semantic_chunks.
- Large corpora could make one query slow.

Needs verification:
- Actual corpus size.
- API worker count.
- Database connection pool settings.
- Query latency under realistic documents.
```

### Remote LightRAG retrieval mode

The remote retrieval engine calls the remote LightRAG server over HTTP.

Assessment:

```text
Safe for 5–10 users:
- The backend can route concurrent requests to the LightRAG server.
- The backend does not itself store or mutate remote embeddings during retrieval.

Risky for 5–10 users:
- The true concurrency limit depends on the LightRAG server, the embedding/LLM provider, and local hardware.
- The current backend does not enforce per-domain rate limits.
- The backend does not provide per-user domain authorization yet.

Needs verification:
- LightRAG service thread/process model.
- LLM provider rate limits.
- Whether graph storage supports concurrent reads during writes.
```

## 05.2 Does retrieval isolate by user?

Current answer:

```text
No strong per-user retrieval isolation is evident in the LightRAG path.
```

The remote retrieval engine ignores `user_id` and routes by domain/document filter.

That may be acceptable if the product model is:

```text
All authenticated users can query shared admin-approved documentation domains.
```

But if different users should see different documents, you need domain ACLs or document ACLs.

For your current stated usage — 5–10 users on a secure local network using shared documentation — shared domains are probably fine.

---

## 06 Admin Upload While Users Retrieve Assessment

## 06.1 Local backend document upload while users retrieve

This is mostly supported by the current architecture if:

```text
INDEX_JOBS_INLINE=false
worker service is running
Redis is available
```

Flow:

```text
Admin uploads document
↓
API saves raw file under STORAGE_ROOT
↓
API creates document row with UPLOADED or INDEXING status
↓
JobService queues an indexing job in Redis/RQ
↓
Worker parses and indexes the document
↓
Parsed output is saved to parsed_documents
↓
Navigation index is saved to navigation_indexes
↓
Semantic chunks are saved to semantic_chunks
↓
Document status becomes READY
```

During that process, normal users can continue querying previously ready documents.

Important safety behavior:

```text
DocumentRepository.list_ready() filters documents by READY status.
```

That means partially indexed documents should not appear in normal ready-document browsing.

## 06.2 Remote LightRAG upload while users retrieve

The backend has remote upload code through:

```text
DocumentService._upload_remote()
LightRAGRemoteAdapter.upload_document()
```

But whether read/write concurrency is safe inside LightRAG itself depends on the remote LightRAG server and its storage backend.

Current backend cannot fully prove that:

```text
User A querying domain manuals
User B querying domain manuals
Admin uploading/indexing new doc into manuals
```

is safe at the LightRAG storage level.

### Recommended safe behavior

Implement this product behavior:

```text
1. Users continue querying the last ready/committed domain state.
2. Admin upload creates a local document row with remote track_id.
3. Backend shows the document as INDEXING.
4. A background status poller checks LightRAG status.
5. When remote status becomes READY, backend marks local document READY.
6. Query UI/TUI shows “domain indexing in progress” without blocking all reads.
7. Only one ingestion job per domain runs at a time unless LightRAG is proven safe for parallel ingestion.
```

This gives you practical safety without over-engineering.

---

## 07 PostgreSQL and Redis Service Analysis

## 07.1 Does LightRAG require separate Postgres and Redis in the current codebase?

Current answer:

```text
No. The current root deployment only defines backend Postgres and backend Redis.
```

The LightRAG domain deployment generator does not add Postgres or Redis services to the generated domain Compose file in the observed code. It generates one service per LightRAG domain and mounts per-domain file storage.

There are unused-looking settings for LightRAG Postgres and Redis URLs in:

```text
app/lightrag_deploy/settings.py
```

But they are not enough to conclude that current LightRAG deployment uses Postgres or Redis.

## 07.2 Service table

| Service | Used By Backend? | Used By LightRAG? | Separate Container Today? | Can Be Shared? | Notes |
|---|---:|---:|---:|---:|---|
| PostgreSQL | Yes | Not clearly in current generated LightRAG compose | One backend container | Yes, if LightRAG is configured to use separate DB/schema | Current local embeddings are in backend DB |
| Redis | Yes | Not clearly in current generated LightRAG compose | One backend container | Yes, with DB index/key prefix separation | Backend uses Redis/RQ for indexing jobs |
| LightRAG service | Only as remote HTTP target | Yes | Not in root compose | N/A | Must be deployed externally or via fixed deployment manager |
| File storage `.data/uploads` | Yes | Local copy before remote upload | Mounted as backend volume | N/A | Backend raw uploads |
| File storage `.data/lightrag/domains` | Intended for LightRAG | Yes, intended | Not root-mounted in main compose | N/A | Per-domain LightRAG state |

## 07.3 Can Postgres and Redis be merged into one shared deployment?

Yes, technically, but only if LightRAG is actually configured to use Postgres and Redis.

For a lightweight local server, there are three options.

### Option A — Separate backend and LightRAG Postgres/Redis services

Use when:

```text
- You want strict operational isolation.
- LightRAG stores are heavy and may need independent backup/restore.
- You expect more users or more domains later.
```

Pros:

- Strong separation.
- Failure in one store less likely to affect the other.
- Easier to reason about ownership.

Cons:

- More containers.
- More ports.
- More backups.
- More env variables.
- More complexity for junior developers.

Recommendation for your current target:

```text
Not recommended as the first implementation unless LightRAG requires it.
```

### Option B — One shared Postgres and one shared Redis, isolated by database/schema/key prefix

Use when:

```text
- LightRAG needs Postgres/Redis.
- You still want a simple deployment.
- You can enforce clean namespace isolation.
```

Recommended isolation:

```text
Postgres:
- database: context_engine
- database: lightrag_default
- database: lightrag_manuals

or:

- database: context_engine
- schema: app
- schema: lightrag_default
- schema: lightrag_manuals

Redis:
- DB 0: context_engine_rq
- DB 1: lightrag_default
- DB 2: lightrag_manuals

or:

- key prefixes:
  ce:rq:*
  lr:default:*
  lr:manuals:*
```

Pros:

- Fewer containers.
- Easier local deployment.
- One backup story for Postgres.
- Good enough for 5–10 local users.

Cons:

- Misconfiguration can cause namespace collision.
- Redis persistence/eviction policy must be chosen carefully.
- DB maintenance affects both backend and LightRAG.

Recommendation:

```text
Good second-stage option if LightRAG external storage is required.
```

### Option C — Backend Postgres/Redis only, LightRAG file-based per domain

Use when:

```text
- You want minimal operational complexity.
- You only have 5–10 users.
- Domains are documentation corpora, not massive enterprise datasets.
- You prefer simple backup folders.
```

Pros:

- Simple.
- Matches the current LightRAG domain deployment code direction.
- Backend database remains clean.
- LightRAG state is isolated by domain folder.
- Easy to back up: backend DB dump + `.data/uploads` + `.data/lightrag`.

Cons:

- Need to understand LightRAG file-storage concurrency.
- File-based storage may not scale to very large corpora.
- Need careful domain-level ingestion locking.

Recommendation:

```text
Recommended first implementation for this app.
```

---

## 08 Recommended Lightweight Deployment Architecture

## Recommended choice

Choose:

```text
Option C first.
```

In implementation-option language:

```text
Option 1: File-based per-domain LightRAG with one backend Postgres and one backend Redis.
```

## 08.1 Target architecture

```text
+-----------------------------+
| Users / Admins              |
| CLI / TUI / Future UI       |
+--------------+--------------+
               |
               v
+-----------------------------+
| Context Engine API          |
| FastAPI                     |
| Auth, documents, query,     |
| admin, LightRAG proxy       |
+------+----------------------+
       |                         
       | local app state          remote domain calls
       v                         v
+--------------+          +--------------------------+
| PostgreSQL   |          | LightRAG Domain: manuals |
| app tables   |          | container/service        |
+--------------+          | storage:                 |
                          | .data/lightrag/domains/  |
+--------------+          | manuals/rag_storage      |
| Redis        |          +--------------------------+
| RQ jobs      |
+--------------+          +--------------------------+
                          | LightRAG Domain: catalog |
                          | container/service        |
                          | storage:                 |
                          | .data/lightrag/domains/  |
                          | catalog/rag_storage      |
                          +--------------------------+
```

## 08.2 Backup model

Back up these three things:

```text
1. Backend PostgreSQL dump
2. .data/uploads
3. .data/lightrag
```

Redis does not usually need durable backup for this use case if it only holds transient jobs. If Redis is later used as durable LightRAG state, this changes.

## 08.3 Why this is best now

Because your app is intended for:

```text
- secure local network;
- 5–10 users;
- admin-managed documentation;
- CLI/TUI backend testing;
- junior-developer maintainability;
- low operational overhead.
```

The simplest design that meets those requirements is better than deploying multiple Postgres/Redis stacks too early.

---

## 09 Required Code or Config Changes

### 09.0 Already implemented (May 2026)

| Item | Status | Evidence |
|---|---|---|
| Deploy settings in config + `.env.example` | Done | `app/core/config.py`, `tests/test_lightrag_deploy_settings.py` |
| Admin domain lifecycle API | Done | `app/api/routes/lightrag_admin.py`, `app/main.py` |
| User domain listing | Done | `GET /lightrag/domains` (safe field subset) |
| Domain manifest + compose generation | Done | `app/lightrag_deploy/service.py`, `tests/test_lightrag_deploy_*` |
| `lightrag_domain_id` on upload/query | Done | `app/api/routes/admin.py`, `app/schemas/query.py` |
| CLI/TUI domain screens | Done | `cli/screens/lightrag_domains.py`, `cli/services/lightrag_domains.py` |

Admin routes (actual module name `lightrag_admin.py`, not `admin_lightrag_domains.py`):

```text
GET    /admin/lightrag/domains
POST   /admin/lightrag/domains
GET    /admin/lightrag/domains/{domain_id}
POST   /admin/lightrag/domains/{domain_id}/up
POST   /admin/lightrag/domains/{domain_id}/down
POST   /admin/lightrag/domains/{domain_id}/recreate
POST   /admin/lightrag/domains/{domain_id}/regenerate
DELETE /admin/lightrag/domains/{domain_id}
DELETE /admin/lightrag/domains/{domain_id}?permanent=true   # when allowed

GET    /lightrag/domains   # any authenticated user; safe metadata only
```

Admin document upload (not under `/admin/lightrag/domains/.../documents/`):

```text
POST /admin/documents/upload
  optional form field: lightrag_domain_id
```

### 09.1 Remaining: explicit upload engine selection

## 09.4 Decide whether document upload should go to backend local RAG or LightRAG

Current `DocumentService.upload()` switches based on:

```text
LIGHTRAG_ENABLED
```

This is too global.

Recommended change:

```text
Admin upload request should explicitly specify target engine:
- local_backend
- lightrag
```

and target domain if LightRAG:

```text
lightrag_domain_id=manuals
```

Today `lightrag_domain_id` is supported when `LIGHTRAG_ENABLED=true`, but the engine is still chosen globally. Avoid relying on a single env flag to switch all uploads.

### 09.2 Remaining: LightRAG status polling or refresh

## 09.5 Add LightRAG status polling or refresh

Remote upload returns a `track_id`.

Add a job or admin action that calls:

```text
LightRAGRemoteAdapter.document_status(track_id)
```

and updates the local `documents.meta.lightrag.status` and local `documents.status`.

Suggested admin route (not implemented yet):

```text
POST /admin/documents/{document_id}/refresh-lightrag-status
```

### 09.3 Remaining: domain-level ingestion lock

## 09.6 Add domain-level ingestion lock

For each domain, only allow one ingestion/indexing job at a time until you prove LightRAG supports parallel same-domain ingestion safely.

This can be implemented with:

```text
Redis lock key: lightrag:domain:<domain_id>:ingest_lock
```

or a database row lock in a future `lightrag_domains` table.

For this app, Redis lock is lightweight and appropriate.

### 09.4 Tests

Implemented (see `tests/`):

```text
[x] Settings load LightRAG deployment values (test_lightrag_deploy_settings.py)
[x] Domain create writes folders, env, manifest, compose (test_lightrag_deploy_*)
[x] Admin domain routes + permissions (test_api.py)
[x] Normal users can list domains (test_api.py)
[x] LightRAG upload stores track_id metadata (test_api.py)
[x] Retrieval by domain uses correct base_url (test_api.py, adapter tests)
```

Still needed:

```text
[ ] Status refresh marks document READY when LightRAG reports processed
[ ] Concurrent upload lock prevents two same-domain ingestion jobs
```

---

## 10 Risks, Unknowns, and Verification Checklist

## 10.1 Key risks

| Risk | Why it matters | Mitigation |
|---|---|---|
| Global `LIGHTRAG_ENABLED` changes upload behavior | Admin may accidentally upload to wrong engine | Add explicit per-upload engine target (`local_backend` vs `lightrag`) |
| No status refresh from `track_id` | Documents may stay `INDEXING` locally after remote success | Add worker or `POST /admin/documents/{id}/refresh-lightrag-status` |
| No same-domain ingest lock | Parallel uploads may be unsafe inside LightRAG | Redis lock `lightrag:domain:<id>:ingest_lock` |
| No domain ACLs | Users may query all listed domains | Add domain access model if needed |
| Unknown LightRAG read/write locking | Admin ingestion may affect user retrieval | One-ingest-at-a-time per domain; verify with LightRAG runtime |
| Local semantic retrieval uses JSON embeddings | Slow for larger corpora | Use real LightRAG or pgvector later |
| No root LightRAG service in compose | `LIGHTRAG_ENABLED=true` may point to nothing | Create domain via admin API, start generated compose, verify health |
| Deploy APIs disabled by default | Operators expect CRUD but get HTTP 400 | Set `LIGHTRAG_DEPLOY_ENABLED=true` when managing domains |

## 10.2 Verification checklist

Before declaring the LightRAG integration production-ready for your local network, verify:

```text
[ ] docker compose up starts backend postgres/redis/api/worker.
[ ] Admin seed works.
[ ] LIGHTRAG_ENABLED=false local upload/index/query works.
[x] A LightRAG domain can be created (admin API + tests).
[x] Domain folders are created under .data/lightrag/domains/<domain_id>/.
[x] Domain env file contains correct WORKSPACE, INPUT_DIR, WORKING_DIR, LOG_DIR.
[x] Domain compose file contains the expected LightRAG service.
[ ] Domain service starts and health check passes (runtime / ops).
[x] LIGHTRAG_DOMAIN_MANIFEST points to generated domains.json.
[x] Backend can resolve domain to correct base_url.
[x] Admin can upload to a LightRAG domain (with lightrag_domain_id).
[x] Backend stores remote document_id and track_id.
[ ] Status refresh eventually marks document READY.
[x] Normal users can list domains and query with lightrag_domain_id.
[ ] Two users can query at the same time (load test).
[ ] Admin upload while users query does not crash retrieval.
[ ] Same-domain double upload is blocked or queued.
[ ] Backups include backend DB, .data/uploads, and .data/lightrag.
```

---

## 11 Junior Developer Explanation

Imagine Context Engine as the control center.

The backend API is the front desk. Users and admins talk to the backend, not directly to the database.

The backend has its own PostgreSQL database. That database stores users, documents, parsed document text, navigation indexes, semantic chunks, jobs, audit logs, and query logs.

The backend also has Redis. Redis is used like a waiting room for background jobs. When an admin uploads a document, the API should not freeze while parsing and indexing happens. Instead, the API can put a job into Redis, and a worker can process that job separately.

Now LightRAG is a separate idea.

LightRAG is not automatically started by the current main Docker Compose file. The backend can talk to a LightRAG server if one is already running. The backend knows where that server is by reading `LIGHTRAG_BASE_URL` or a domain manifest file.

The deployment package (`app/lightrag_deploy/`) creates one LightRAG container per domain when operators use the admin API or TUI. A domain is like a named knowledge base. For example:

```text
manuals
catalogs
policies
```

Each domain gets its own folder:

```text
.data/lightrag/domains/manuals/
```

Inside that folder, the important subfolder is:

```text
rag_storage
```

That is where the LightRAG service is expected to store its internal indexed knowledge, embeddings, and graph data.

So the recommended simple mental model is:

```text
PostgreSQL = Context Engine app database
Redis = Context Engine background job queue
.data/uploads = local copies of uploaded files
.data/lightrag/domains/<domain>/rag_storage = LightRAG domain knowledge storage
```

For 5–10 users, this is a good model. Do not add separate Postgres and Redis for LightRAG unless LightRAG actually needs them and you have confirmed the config.

When users retrieve context, they are mostly reading. Multiple users reading at the same time should be okay for a small local system, assuming the LightRAG service and LLM provider can handle the requests.

When an admin uploads new documentation, that is a write/indexing operation. Writes are more dangerous than reads. The safe design is to let old content remain queryable while the new document is indexing. When indexing finishes, the new document becomes available.

That is why the app should track document status:

```text
UPLOADED
INDEXING
READY
FAILED
```

Users should only retrieve from ready content. Admins should be able to see indexing progress.

---

## Final Recommendation

Use this implementation path first:

```text
One backend PostgreSQL service.
One backend Redis service.
One Context Engine API service.
One Context Engine worker service.
One LightRAG container per domain only when needed.
LightRAG domain data stored under .data/lightrag/domains/<domain_id>/.
```

Do not deploy separate Postgres/Redis services for LightRAG at this stage.

Do not merge LightRAG into backend Postgres/Redis until there is a confirmed requirement and official LightRAG configuration for that storage mode.

Option 1 core wiring is in place (admin API, TUI, manifest, compose generation). Next: status refresh from `track_id`, per-domain ingest lock, and optional explicit per-upload engine selection.
