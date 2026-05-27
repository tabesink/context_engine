# 05 — Coding Agent Prompt

Use this prompt with a coding agent.

```text
You are a senior backend engineer working in the repository:

https://github.com/tabesink/context_engine.git

Task: implement Option B for managed LightRAG domains: Postgres-backed LightRAG storage with explicit per-domain Postgres provisioning.

Current observed error:

postgres-1 | FATAL: password authentication failed for user "lightrag"
postgres-1 | DETAIL: Role "lightrag" does not exist.

This means a LightRAG domain container is reaching Postgres but the generated domain env points to a DB role that was never provisioned.

Implement the clean fix. Do not just reuse the app's context_engine user/database unless an explicit shared_runtime mode is selected. Default should be per-domain provisioning.

Required changes:

1. Add explicit settings:
   - LIGHTRAG_STORAGE_BACKEND=postgres
   - LIGHTRAG_POSTGRES_PROVISIONING_MODE=per_domain
   - LIGHTRAG_POSTGRES_VECTOR_INDEX_TYPE=HNSW

2. Update app/core/config.py and app/lightrag_deploy/settings.py.

3. Update app/lightrag_deploy/compose.py so generated domain.env uses domain.postgres_database and domain.postgres_user in per_domain mode. It must not silently use settings.runtime_postgres_database/settings.runtime_postgres_user for per-domain LightRAG storage.

4. Add app/lightrag_deploy/postgres_provisioner.py:
   - use psycopg with autocommit
   - use psycopg.sql.Identifier for identifiers
   - ensure role exists
   - ensure database exists
   - grant required privileges
   - create extensions vector and AGE in the domain database when available
   - return structured diagnostics
   - be idempotent

5. Wire provisioner into app/lightrag_deploy/service.py:
   - create_domain provisions before writing domain.env
   - regenerate provisions before rewriting domain.env
   - repair normalizes old manifests, provisions, regenerates, recreates/starts the domain, and returns diagnostics

6. Add route:
   POST /admin/lightrag/domains/{domain_id}/repair

7. Add tests:
   - env renders domain-level Postgres DB/user
   - provisioner idempotent SQL behavior
   - repair endpoint returns diagnostics
   - existing domain missing postgres fields is normalized

Acceptance:

- A fatigue domain generates POSTGRES_DATABASE=lightrag_fatigue and POSTGRES_USER=lightrag_fatigue.
- Postgres has role lightrag_fatigue.
- Postgres has database lightrag_fatigue.
- LightRAG container can connect without `Role "lightrag" does not exist`.
- Repair endpoint can be run repeatedly without breaking state.

Keep the implementation lean and junior-readable. Avoid duplicating URL/domain resolution logic. Keep Context Engine app state and LightRAG RAG persistence clearly separated.
```
