# 3. Main Functional Flows

## Flow A: Admin User Seed

Likely path:

```text
python -m scripts.seed_admin
        │
        ▼
get_settings()
        │
        ▼
UserRepository.create(... role=ADMIN ...)
        │
        ▼
users table
```

Environment/settings involved:

- `SEED_ADMIN_EMAIL`
- `SEED_ADMIN_PASSWORD`
- `DATABASE_URL`

Security behavior:

- Passwords are hashed through `app.core.security.hash_password`.
- The code uses `passlib` with `pbkdf2_sha256`.

## Flow B: User Login

```text
POST /auth/login
  body: { email, password }
        │
        ▼
UserRepository.get_by_email(email)
        │
        ▼
verify_password(password, user.password_hash)
        │
        ▼
create_access_token(user_id, email, role)
        │
        ▼
return bearer JWT
```

Failure modes:

- Unknown email -> unauthorized.
- Invalid password -> unauthorized.
- Later request with invalid/expired token -> unauthorized.
- Token user id missing or inactive user -> unauthorized.

Token payload includes:

- `sub`: user id
- `email`
- `role`
- `exp`

## Flow C: Authenticated Request

```text
Client sends Authorization: Bearer <token>
        │
        ▼
OAuth2PasswordBearer(tokenUrl="/auth/login")
        │
        ▼
decode_access_token(token)
        │
        ▼
UserRepository.get_by_id(sub)
        │
        ▼
active user returned to route
```

For admin routes:

```text
get_current_user()
        │
        ▼
require_admin()
        │
        ├── role == admin -> allow
        └── else -> 403 Forbidden
```

## Flow D: Admin Uploads a Document — Local Indexing Disabled/Queued Case

When `LIGHTRAG_ENABLED=false`, upload follows the local pipeline.

```text
POST /admin/documents/upload
        │
        ▼
require_admin()
        │
        ▼
DocumentService.upload(file, actor)
        │
        ▼
FileStorage.save_upload(file)
        │
        ▼
DocumentRepository.create(... status=uploaded ...)
        │
        ▼
LogRepository.record_audit("document.uploaded")
        │
        ▼
JobService.enqueue_index_document(document_id)
        │
        ├── INDEX_JOBS_INLINE=true
        │       └── run indexing immediately in API process
        │
        └── INDEX_JOBS_INLINE=false
                └── enqueue RQ job in Redis queue `indexing`
```

Response includes:

- document metadata
- `job_id`

## Flow E: Admin Uploads a Document — Remote LightRAG Enabled

When `LIGHTRAG_ENABLED=true`, `DocumentService.upload` calls `_upload_remote`.

```text
POST /admin/documents/upload
        │
        ▼
FileStorage.save_upload(file)
        │
        ▼
DocumentRepository.create(... status=indexing ...)
        │
        ▼
LightRAGRemoteAdapter.for_domain(...).upload_document(...)
        │
        ▼
record remote lightrag metadata on local document
        │
        ▼
return document with job_id=None
```

Important behavior:

- The local app still creates a local `documents` row.
- Remote LightRAG upload response metadata is stored under the document metadata key, such as `metadata["lightrag"]`.
- If remote upload fails, the document is marked failed and an HTTP error is returned.

## Flow F: Local Document Indexing

```text
IndexingService.index_document(document_id)
        │
        ▼
DocumentRepository.get(document_id)
        │
        ▼
DocumentRepository.set_status(INDEXING)
        │
        ▼
DocumentParser.parse(storage_path)
        │
        ▼
save parsed document
        │
        ▼
NavigationIndexBuilder builds tree
        │
        ▼
save navigation index
        │
        ▼
SemanticIndexBuilder builds chunks/embeddings
        │
        ▼
replace semantic chunks
        │
        ▼
set document status READY
```

Failure behavior:

```text
exception during parse/index/build
        │
        ▼
DocumentRepository.set_status(FAILED, error=str(exc))
        │
        ▼
exception re-raised to caller/worker
```

## Flow G: Worker Processes Queued Index Job

```text
app.workers.worker
        │
        ▼
Redis.from_url(settings.redis_url)
        │
        ▼
Worker(["indexing"])
        │
        ▼
app.workers.tasks.run_index_job(job_id)
        │
        ▼
JobRepository.set_status(RUNNING)
        │
        ▼
IndexingService.index_document(document_id)
        │
        ├── success -> JobRepository.set_status(SUCCEEDED)
        └── exception -> JobRepository.set_status(FAILED, error_message=str(exc))
```

## Flow H: User Lists and Reads Documents

```text
GET /documents
        │
        ▼
get_current_user()
        │
        ▼
DocumentRepository.list_ready()
        │
        ▼
return only READY documents
```

For detail, structure, and page APIs, `DocumentService.get_ready_or_404` prevents users from seeing non-ready documents.

This is a good boundary for normal users.

## Flow I: User Retrieval Query

```text
POST /query/retrieve
        │
        ▼
get_current_user()
        │
        ▼
RetrievalService.retrieve(request, user)
        │
        ▼
RetrievalRoutingPolicy chooses backend/mode
        │
        ├── local semantic/navigation/hybrid engines
        └── remote LightRAG engine if enabled/selected
        │
        ▼
return RetrieveResponse with evidence
        │
        ▼
LogRepository.record_query(... latency/evidence_count ...)
```

Modes likely include:

- `auto`
- `semantic`
- `navigation`
- `hybrid`

## Flow J: User Answer Query

```text
POST /query/answer or POST /query
        │
        ▼
RetrievalService.answer(request, user)
        │
        ▼
retrieve evidence
        │
        ▼
AnswerComposer builds answer from evidence
        │
        ▼
return QueryResponse
```

Current answer composition appears intentionally lightweight: it composes an answer from evidence rather than necessarily calling an external LLM in the reviewed path.

## Flow K: CLI Calls Backend

```text
ragcli login --email ... --password ...
        │
        ▼
POST /auth/login
        │
        ▼
CredentialStore saves base_url + token
        │
        ├── OS keyring if available
        └── ~/.context-engine/ragcli/credentials.json fallback
```

Then:

```text
ragcli documents list
        │
        ▼
load token
        │
        ▼
GET /documents with Authorization header
```

CLI is not a separate backend. It is an API client and test/admin tool.
