# 7. Coding Agent Checklist and Safe Codebase Index

Use this before asking an agent to modify the repository.

## 7.1 Before Modifying Auth

Read:

- `app/api/routes/auth.py`
- `app/api/deps.py`
- `app/core/security.py`
- `app/storage/repositories/users.py`
- `app/domain/models.py`
- `tests/test_api.py`

Rules:

- Login returns a bearer JWT.
- Token contains user id, email, role, and expiry.
- Every authenticated request reloads user from DB.
- `require_admin` is the admin boundary.
- Do not let admin-only operations bypass `require_admin`.

Safe changes:

- Better error messages.
- Stronger production config validation.
- More tests around expired/invalid tokens.

Dangerous changes:

- Changing token payload shape without updating deps/tests/CLI.
- Changing role strings without migration/tests.
- Storing plaintext passwords.

## 7.2 Before Modifying Document Uploads

Read:

- `app/api/routes/admin.py`
- `app/services/document_service.py`
- `app/services/file_storage.py`
- `app/services/job_service.py`
- `app/integrations/lightrag_remote_adapter.py`
- `tests/test_api.py`

Rules:

- Only admin users upload documents.
- Local mode saves file, creates document row, audits upload, then enqueues/runs indexing.
- LightRAG mode saves file, creates local doc row, uploads to LightRAG, stores remote metadata.
- Upload should return a document and possibly a `job_id`.

Safe changes:

- Add file size/type validation.
- Normalize filenames.
- Improve error messages.
- Add tests for unsupported files.

Dangerous changes:

- Removing local document row creation in LightRAG mode without updating query/docs behavior.
- Starting indexing before file storage is complete.
- Returning inconsistent document status.

## 7.3 Before Modifying Indexing

Read:

- `app/services/indexing_service.py`
- `app/indexing/parsers.py`
- `app/indexing/navigation_index_builder.py`
- `app/indexing/semantic_index_builder.py`
- `app/indexing/chunking.py`
- `app/storage/repositories/documents.py`
- `app/workers/tasks.py`
- `tests/test_api.py`

Rules:

- Indexing sets document status to `INDEXING`.
- On success, parsed doc, nav index, semantic chunks are saved and document status becomes `READY`.
- On failure, document status becomes `FAILED`.
- Worker updates job status separately.

Safe changes:

- Better chunk metadata.
- More parser support.
- Transactional chunk replacement.
- Duplicate reindex guard.

Dangerous changes:

- Partial writes without rollback strategy.
- Deleting old chunks before new chunks are ready unless transaction-protected.
- Running long indexing in API process when queued mode is expected.

## 7.4 Before Modifying Retrieval/Query

Read:

- `app/api/routes/query.py`
- `app/services/retrieval_service.py`
- `app/retrieval/router.py`
- `app/retrieval/routing_policy.py`
- `app/retrieval/semantic_engine.py`
- `app/retrieval/navigation_engine.py`
- `app/retrieval/hybrid_merger.py`
- `app/retrieval/lightrag_remote_engine.py`
- `app/retrieval/answer_composer.py`
- `app/schemas/query.py`
- `tests/test_retrieval_routing_policy.py`
- `tests/test_answer_composer.py`
- `tests/test_evidence_mapper.py`

Rules:

- `/query/retrieve` returns evidence/context.
- `/query/answer` and `/query` return answer + evidence.
- Local and remote retrieval are selected through routing policy.
- Query logs record mode, latency, and evidence count.
- Debug output should only appear for admins.

Safe changes:

- Improve answer format.
- Add source citations or evidence formatting.
- Tune routing policy with tests.

Dangerous changes:

- Leaking debug info to normal users.
- Bypassing query logging accidentally.
- Breaking CLI payload shape.

## 7.5 Before Modifying LightRAG Integration

Read:

- `app/api/routes/lightrag.py`
- `app/integrations/lightrag_remote_adapter.py`
- `app/integrations/lightrag_domains.py`
- `app/retrieval/lightrag_remote_engine.py`
- `app/core/config.py`
- `tests/test_lightrag_remote_adapter.py`
- LightRAG-related tests in `tests/test_api.py`

Rules:

- Context Engine should remain the orchestration layer.
- LightRAG should remain behind adapter files.
- Do not tangle LightRAG-specific HTTP calls across route/service code.
- Graph proxy paths currently mirror upstream paths.

Safe changes:

- Add env examples.
- Add timeout/retry tests.
- Add domain config docs.
- Add admin status check for LightRAG health.

Dangerous changes:

- Scattering LightRAG calls across unrelated modules.
- Making local mode depend on LightRAG being installed/running.
- Changing upstream path names without frontend/CLI/docs updates.

## 7.6 Before Modifying Jobs/Workers

Read:

- `app/services/job_service.py`
- `app/workers/tasks.py`
- `app/workers/worker.py`
- `app/storage/repositories/jobs.py`
- `app/domain/models.py`
- `tests/test_api.py`

Rules:

- Inline mode is useful for tests.
- Queued mode requires Redis and worker.
- Job status and document status are both important.
- Failed jobs should preserve error messages.

Safe changes:

- Add duplicate job guard.
- Add worker heartbeat/status.
- Improve retry behavior.

Dangerous changes:

- Making tests require Redis.
- Removing inline mode.
- Retrying failed jobs without resetting status cleanly.

## 7.7 Before Modifying CLI

Read:

- `cli/main.py`
- `cli/api_client.py`
- `cli/credentials.py`
- `pyproject.toml`
- `tests/test_cli*.py`

Rules:

- CLI calls API; it should not duplicate backend business logic.
- Auth token is stored through `CredentialStore`.
- `--output json` is important for scripting/tests.
- Placeholder commands return `not_supported_by_backend`.

Safe changes:

- Better help text.
- Hide/label unsupported commands.
- Add command examples.
- Add admin system status command after backend exists.

Dangerous changes:

- Hardcoding localhost without `--api-base-url` option.
- Removing JSON output mode.
- Storing credentials insecurely without warning.

## 7.8 Before Modifying Config/Deployment

Read:

- `app/core/config.py`
- `.env.example`
- `docker-compose.yml`
- `Dockerfile`
- `README.md`

Rules:

- Code defaults support simple local SQLite mode.
- `.env.example` supports PostgreSQL/Redis compose mode.
- Worker and API must share DB, Redis, and storage config.
- `STORAGE_ROOT` must persist uploaded files.

Safe changes:

- Add missing env examples.
- Add production config validation.
- Add deployment docs.
- Add system status route.

Dangerous changes:

- Changing default env names without updating compose/README/tests.
- Making local tests require external services.
- Breaking `uvicorn app.main:create_app --factory` startup.

## 7.9 Before Modifying Tests

Read:

- `tests/test_api.py`
- `tests/test_cli*.py`
- `tests/test_lightrag_remote_adapter.py`
- `tests/test_retrieval_routing_policy.py`
- `tests/test_answer_composer.py`
- `tests/test_evidence_mapper.py`

Rules:

- Keep tests fast.
- Keep SQLite/in-memory-ish local behavior for core API tests.
- Use monkeypatch for remote LightRAG behavior.
- Do not require real Redis/LightRAG for ordinary unit tests.

Safe additions:

- Config guard tests.
- Upload validation tests.
- Duplicate job guard tests.
- Admin system status tests with mocked Redis/LightRAG.

Dangerous changes:

- Tests requiring external services by default.
- Tests that depend on ordering without explicit sort.
- Tests that leave `.data/test_context_engine.db` dirty.

# 7.10 Golden Rule for Future Agents

Before changing any subsystem, the agent must answer:

1. Which route or CLI command exercises this behavior?
2. Which service owns the business logic?
3. Which repository/table persists the state?
4. Which tests currently protect it?
5. What backward compatibility must be preserved for CLI and future frontend clients?

If the agent cannot answer these, it should map the code first before editing.
