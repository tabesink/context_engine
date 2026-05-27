# Context Engine — LightRAG Postgres Option B Full Handoff

## Executive summary

The current error:

```text
FATAL: password authentication failed for user "lightrag"
DETAIL: Role "lightrag" does not exist.
```

means the managed LightRAG container can reach Postgres but is using credentials that Postgres has not provisioned.

Implement Option B as:

```text
Managed LightRAG domains use Postgres storage.
Context Engine provisions the matching DB role and database before the domain starts.
Generated domain.env must use the same provisioned DB identity.
Repair can safely re-run provisioning and recreate the domain.
```

## Current bug pattern

Current code mixes three DB identities:

```text
context_engine       # app DB/user from DATABASE_URL
lightrag             # default LightRAG DB user from settings/env
lightrag_fatigue     # intended per-domain DB/user
```

That is why a generated or stale `domain.env` can point at `POSTGRES_USER=lightrag` while Postgres only knows `context_engine`.

## Recommended target

For domain `fatigue`:

```env
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DATABASE=lightrag_fatigue
POSTGRES_USER=lightrag_fatigue
POSTGRES_PASSWORD=<LIGHTRAG_POSTGRES_PASSWORD>
```

## Why not just use context_engine?

Using the app runtime `context_engine` user can unblock quickly, but it blurs the boundary between app state and LightRAG index state.

Use `context_engine` only if you explicitly introduce `LIGHTRAG_POSTGRES_PROVISIONING_MODE=shared_runtime`.

Default should be:

```env
LIGHTRAG_POSTGRES_PROVISIONING_MODE=per_domain
```

## Implementation checklist

1. Add explicit settings.
2. Add Postgres provisioner.
3. Render `domain.env` from domain-level Postgres fields.
4. Provision before create/regenerate/repair.
5. Add `POST /admin/lightrag/domains/{domain_id}/repair`.
6. Add tests.
7. Run repair for existing domains.

## Files to edit

```text
app/core/config.py
app/lightrag_deploy/settings.py
app/lightrag_deploy/compose.py
app/lightrag_deploy/service.py
app/lightrag_deploy/models.py
app/api/routes/lightrag_admin.py
.env.example
```

## New file

```text
app/lightrag_deploy/postgres_provisioner.py
```

## Tests to add

```text
tests/lightrag_deploy/test_postgres_domain_env.py
tests/lightrag_deploy/test_postgres_provisioner.py
tests/api/test_lightrag_admin_repair.py
```

## Immediate runbook

```bash
./scripts/diagnose_lightrag_postgres.sh fatigue
```

Then, after implementation:

```bash
curl -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8010/admin/lightrag/domains/fatigue/repair
```

Expected generated env:

```bash
grep -E "POSTGRES_DATABASE|POSTGRES_USER" .data/lightrag/domains/fatigue/domain.env
```

```env
POSTGRES_DATABASE=lightrag_fatigue
POSTGRES_USER=lightrag_fatigue
```

## Acceptance criteria

- No Postgres log says `Role "lightrag" does not exist`.
- `lightrag_fatigue` role exists.
- `lightrag_fatigue` database exists.
- `vector` extension is created where available.
- `AGE` extension is created where available.
- Upload and graph retrieval work after repair.
- `repair` is idempotent.
