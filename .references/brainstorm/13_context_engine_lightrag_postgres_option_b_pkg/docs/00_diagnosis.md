# 00 — Diagnosis

## Error observed

```text
worker-1         | Successfully completed app.workers.tasks.run_document_ingest_job(...)
worker-1         | indexing: Job OK (...)
postgres-1       | FATAL:  password authentication failed for user "lightrag"
postgres-1       | DETAIL: Role "lightrag" does not exist.
```

## What this means

This means the LightRAG domain container is reaching Postgres, but it is trying to authenticate as a role that Postgres does not have.

This is not the same as the earlier DNS issue where the API container could not resolve `lightrag_fatigue`.

Current state implied by the log:

```text
API/worker -> LightRAG domain: likely reachable now
LightRAG domain -> Postgres: reachable
LightRAG domain -> Postgres auth: failing
```

## Why the current code makes this likely

The current LightRAG domain creation code creates domain metadata with per-domain fields such as:

```python
postgres_database=f"{settings.postgres_database_prefix}_{domain_id}"
postgres_user=f"{settings.postgres_user_prefix}_{domain_id}"
```

But the generated `domain.env` logic currently prefers app runtime database credentials in places where it should use the domain-level values. That creates ambiguity between:

```text
context_engine       # app database/user
lightrag             # default LightRAG user from settings/env
lightrag_fatigue     # intended per-domain LightRAG user
```

## Correct interpretation of the user's finding

The user's finding is directionally correct:

> The LightRAG container is trying to connect as `lightrag`, but that role does not exist.

However, the recommended clean fix is not simply “use `context_engine` everywhere.” That would mix app tables and LightRAG persistence in one database/user unless done deliberately.

## Clean Option B fix

The clean fix is:

```text
1. Make Postgres-backed LightRAG storage explicit.
2. Provision the role/database before starting the domain.
3. Generate domain.env from provisioned domain credentials.
4. Add a repair operation that can re-run provisioning safely.
```

