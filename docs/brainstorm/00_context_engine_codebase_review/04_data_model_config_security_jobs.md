# 4. Data Model, Configuration, Security, and Jobs

## 4.1 Database Setup

Database setup lives in:

- `app/storage/db.py`
- `app/storage/tables.py`

Key behavior:

- Uses SQLAlchemy ORM.
- `Settings.database_url` controls the backend database.
- SQLite is the default in code: `sqlite:///./.data/context_engine.db`.
- `.env.example` points to PostgreSQL: `postgresql+psycopg://context_engine:context_engine@localhost:5432/context_engine`.
- `create_db_and_tables()` imports table definitions and runs `Base.metadata.create_all(bind=engine)`.

Design implication:

- This is simple and good for early/local use.
- For production-like deployments, consider adding Alembic migrations before schema changes become risky.

## 4.2 Table Inventory

| Table/Model | Purpose | Important Fields | Created/Updated By |
|---|---|---|---|
| `users` / `UserRow` | User accounts and roles. | `id`, `email`, `password_hash`, `role`, `is_active`, `created_at` | `UserRepository`, seed script. |
| `documents` / `DocumentRow` | Document metadata and lifecycle state. | `id`, `owner_id`, `filename`, `content_type`, `storage_path`, `status`, `active_index_version`, `error`, `metadata`, timestamps | `DocumentService`, `DocumentRepository`, `IndexingService`. |
| `parsed_documents` / `ParsedDocumentRow` | Parsed page/full-text representation. | `document_id`, `title`, `pages`, `full_text`, `metadata` | `IndexingService`. |
| `navigation_indexes` / `NavigationIndexRow` | Navigation/tree index per document. | `document_id`, `version`, `tree` | `IndexingService`, `NavigationIndexBuilder`. |
| `semantic_chunks` / `SemanticChunkRow` | Searchable chunks and simple embeddings. | `id`, `document_id`, `chunk_index`, `text`, `embedding`, `page_start`, `page_end`, `score_hint`, `metadata` | `IndexingService`, `SemanticIndexBuilder`. |
| `jobs` / `JobRow` | Indexing jobs. | `id`, `kind`, `status`, `document_id`, `error_message`, `metadata`, timestamps | `JobService`, worker tasks. |
| `audit_logs` / `AuditLogRow` | Admin/audit events. | `id`, `actor_id`, `event`, `target_id`, `metadata`, `created_at` | `LogRepository.record_audit`. |
| `query_logs` / `QueryLogRow` | Retrieval/query usage logs. | `id`, `user_id`, `query`, `mode`, `latency_ms`, `evidence_count`, `created_at` | `RetrievalService`, `LogRepository.record_query`. |

## 4.3 Data Model Observations

Strong points:

- Core runtime tables are concentrated in `app/storage/tables.py`.
- Repositories isolate most direct database access.
- Document status and job status make lifecycle tracking explicit.
- Query and audit logs are present, which is useful for a multi-user app.

Risks / watch items:

- Automatic table creation is convenient but weak for controlled production schema evolution.
- Semantic embeddings are stored as JSON lists. This is okay for lightweight local search, but it does not use pgvector similarity indexes directly in the reviewed code path.
- `metadata` columns can become messy if not documented with a clear structure.
- Concurrent reindexing of the same document should be guarded if multiple admins are expected to trigger operations at the same time.

## 4.4 Configuration Inventory

Settings live in `app/core/config.py` and are loaded from `.env` through Pydantic settings.

| Setting | Default in Code | In `.env.example`? | Purpose | Concern |
|---|---|---:|---|---|
| `APP_NAME` | `Context Engine` | Yes | FastAPI app title/name. | Low risk. |
| `ENVIRONMENT` | `local` | Yes | Environment label. | Could be used more for prod checks. |
| `SECRET_KEY` | `change-me` | Yes | JWT signing key. | Must change for deployment. |
| `ACCESS_TOKEN_MINUTES` | `60` | Yes | JWT expiry. | Good. |
| `DATABASE_URL` | SQLite `.data/context_engine.db` | Yes, PostgreSQL | DB connection. | Difference between code default and compose env should be documented. |
| `REDIS_URL` | `redis://localhost:6379/0` | Yes | RQ worker/queue. | Required if not inline. |
| `INDEX_JOBS_INLINE` | `False` | Yes | Inline vs queued indexing. | Tests use true; deploy likely false. |
| `STORAGE_ROOT` | `.data/uploads` | Yes | Upload file storage. | Must be persistent in deployment. |
| `ALLOWED_ORIGINS` | `['*']` | Yes | CORS origins. | Tighten if exposed beyond local network. |
| `SEED_ADMIN_EMAIL` | `admin@example.com` | Yes | Seed script admin email. | Change for real deployment. |
| `SEED_ADMIN_PASSWORD` | `admin-password` | Yes | Seed script admin password. | Change immediately. |
| `LIGHTRAG_ENABLED` | `False` | Not clearly present | Enable remote LightRAG route for retrieval/upload. | Add to `.env.example`. |
| `LIGHTRAG_BASE_URL` | `http://localhost:9621` | Not clearly present | Remote LightRAG service URL. | Add to `.env.example`. |
| `LIGHTRAG_API_KEY` | `None` | Not clearly present | Optional LightRAG auth. | Add to `.env.example` if used. |
| `LIGHTRAG_DOMAIN` | `default` | Not clearly present | Default LightRAG domain. | Add to `.env.example`. |
| `LIGHTRAG_DOMAIN_MANIFEST` | `None` | Not clearly present | Domain manifest path. | Add to docs. |
| `LIGHTRAG_TIMEOUT_SECONDS` | `10.0` | Not clearly present | Remote timeout. | Add to docs. |

## 4.5 Auth and Security Review

Auth files:

- `app/core/security.py`
- `app/api/deps.py`
- `app/api/routes/auth.py`
- `app/storage/repositories/users.py`

Observed behavior:

- Password hashing uses `passlib` with `pbkdf2_sha256`.
- JWTs are signed with `SECRET_KEY` and algorithm `HS256`.
- Token includes user id, email, role, and expiry.
- Current user is loaded from DB on each authenticated request.
- Inactive users are blocked.
- Admin routes call `require_admin`.

Good enough for:

- Small local-network multi-user app.
- Admin-only upload/index actions.
- CLI/future frontend bearer-token auth.

Improve soon:

- Ensure real deployment never uses default `SECRET_KEY` or seed credentials.
- Document token storage risk in CLI fallback file.
- Add a startup warning or failure when `ENVIRONMENT=production` and `SECRET_KEY` is default.
- Consider file upload validation by extension, size, and MIME type.

Not necessary yet unless internet-facing:

- Complex OAuth/OIDC.
- Multi-tenant isolation.
- Enterprise audit controls.
- Fine-grained per-document permissions.

## 4.6 Background Jobs and Concurrency

Job files:

- `app/services/job_service.py`
- `app/workers/tasks.py`
- `app/workers/worker.py`
- `app/storage/repositories/jobs.py`

Modes:

### Inline mode

```text
INDEX_JOBS_INLINE=true
```

- Upload/index request runs indexing immediately in the API process.
- Useful for tests and very small/simple local runs.
- Simpler but can block requests during parsing/indexing.

### Queued mode

```text
INDEX_JOBS_INLINE=false
```

- `JobService` creates a job row.
- Enqueues `app.workers.tasks.run_index_job` into RQ queue `indexing` using Redis.
- Worker process consumes jobs and updates status.

Failure behavior:

- Worker sets job status `FAILED` and records error message.
- Indexing service marks document status `FAILED` when indexing exceptions occur.

Concurrency risks to watch:

| Risk | Current Situation | Lightweight Fix |
|---|---|---|
| Two admins reindex same document at same time | Possible unless repository/service prevents it elsewhere. | Add guard: reject if same document has queued/running index job. |
| Worker down while jobs queued | Jobs remain queued; admin can inspect jobs. | Add readiness/admin warning for worker/Redis. |
| API process blocks in inline mode | Expected. | Use inline only for tests/dev; queued for deployment. |
| User queries while document indexing | Normal user document APIs hide non-ready documents. Retrieval should ignore non-ready chunks if indexing replacement is safe. | Ensure chunk replacement is transaction-safe. |
| File deleted while indexing | Possible if delete/reindex race. | Add status guard or transaction boundary. |

## 4.7 Recommended Lightweight Config Direction

For your goal of easy deployment to another machine:

1. Keep one `.env` per deployment environment.
2. Keep `.env.example` comprehensive and documented.
3. Add `.env.local.example` and `.env.production.example` if dev/prod switching is becoming confusing.
4. Keep code defaults safe for local use, but enforce production checks when `ENVIRONMENT=production`.
5. Add an admin `/health/readiness` or `/admin/system/status` endpoint that reports:
   - DB reachable
   - Redis reachable if queued jobs enabled
   - storage root writable
   - LightRAG reachable if enabled
   - worker heartbeat if available
