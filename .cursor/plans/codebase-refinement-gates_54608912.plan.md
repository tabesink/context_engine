---
name: codebase-refinement-gates
overview: Refine the codebase around a lean default operator path, remove stale/unsupported config and API surfaces, and add production guardrails without adding architectural complexity.
todos:
  - id: p0-env-split
    content: Trim `.env.example`, add split LightRAG deploy/provider example files, and align documented/default API port behavior.
    status: completed
  - id: p1-remove-lightrag-enabled
    content: Remove `LIGHTRAG_ENABLED` from config/code/tests and enforce explicit LightRAG connectivity requirements.
    status: completed
  - id: p2-prod-guardrails
    content: Implement production-only settings validation, PostgreSQL-only runtime DB policy, and dev/prod Docker/Compose behavior separation.
    status: completed
  - id: p3-readiness-and-bounds
    content: Add dependency-aware readiness checks, endpoint pagination limits, and query-log safety/retention controls.
    status: completed
  - id: docs-drift-cleanup
    content: Update README/deployment/brainstorm docs to match runtime truth and reduced default config surface.
    status: completed
isProject: false
---

# Codebase Refinement Plan (Design Gates Locked)

## Confirmed Gate Decisions
- `.env.example` stays **host-first** for local operators.
- `LIGHTRAG_ENABLED` is removed **end-to-end** (examples/docs + `Settings` field/validation branches).
- Retrieval public API remains **`POST /retrieve` only**.
- Context Engine runtime DB support is **PostgreSQL-only** (local/staging/production); SQLite fallback is removed.

## Current-State Corrections From Validation
- `.env.example` formatting is already one assignment per line (no malformed multi-var lines).
- `/query/*` routes are already removed in runtime and covered by 404 tests.
- Main entropy is now config surface, production safety defaults, unbounded list endpoints, readiness depth, and doc drift.

## Phase P0 — Lean Config Surface + Drift Elimination
- Reduce default env surface in [`/data/home/tkodippili/Desktop/localTest_context_engine/.env.example`](/data/home/tkodippili/Desktop/localTest_context_engine/.env.example) to common operator settings only (app/auth/db/redis/storage/cors/seed + runtime LightRAG connectivity).
- Add advanced split examples:
  - [`/data/home/tkodippili/Desktop/localTest_context_engine/.env.lightrag-deploy.example`](/data/home/tkodippili/Desktop/localTest_context_engine/.env.lightrag-deploy.example)
  - [`/data/home/tkodippili/Desktop/localTest_context_engine/.env.lightrag-provider.example`](/data/home/tkodippili/Desktop/localTest_context_engine/.env.lightrag-provider.example)
- Keep host-first defaults in `.env.example` and explicitly document compose-network variants in [`/data/home/tkodippili/Desktop/localTest_context_engine/docs/deployment.md`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/deployment.md).
- Align API port contract across:
  - [`/data/home/tkodippili/Desktop/localTest_context_engine/.env.example`](/data/home/tkodippili/Desktop/localTest_context_engine/.env.example)
  - [`/data/home/tkodippili/Desktop/localTest_context_engine/README.md`](/data/home/tkodippili/Desktop/localTest_context_engine/README.md)
  - [`/data/home/tkodippili/Desktop/localTest_context_engine/docker-compose.yml`](/data/home/tkodippili/Desktop/localTest_context_engine/docker-compose.yml)
  - [`/data/home/tkodippili/Desktop/localTest_context_engine/cli/config.py`](/data/home/tkodippili/Desktop/localTest_context_engine/cli/config.py)

## Phase P1 — Remove Unsupported/Illusory Surfaces
- Remove `LIGHTRAG_ENABLED` from settings and env parsing in [`/data/home/tkodippili/Desktop/localTest_context_engine/app/core/config.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/core/config.py).
- Replace current validator semantics with explicit required-runtime checks (e.g., `LIGHTRAG_BASE_URL` or resolvable domain manifest) in the same settings module.
- Update tests that currently assert `LIGHTRAG_ENABLED=false` rejection and replace with assertions on required LightRAG connectivity contract in [`/data/home/tkodippili/Desktop/localTest_context_engine/tests/test_api.py`](/data/home/tkodippili/Desktop/localTest_context_engine/tests/test_api.py).
- Preserve and strengthen retrieval API contract (`/retrieve` mounted, `/query/*` absent) in route/API tests.

## Phase P1.5 — Remove SQLite Runtime Fallback (Entropy Cut)
- In [`/data/home/tkodippili/Desktop/localTest_context_engine/app/core/config.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/core/config.py), make `database_url` explicit (no code-level sqlite default) so startup fails fast when `DATABASE_URL` is missing/malformed.
- Enforce database policy in settings validation:
  - reject `sqlite://` for `ENVIRONMENT` in `local`, `development`, `staging`, and `production`
  - allow sqlite only for explicitly isolated `ENVIRONMENT=test` flows if still required by tests
- In [`/data/home/tkodippili/Desktop/localTest_context_engine/app/storage/db.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/storage/db.py), remove sqlite-specific `.data` directory creation and keep engine URL resolution strictly from validated settings.
- Align supporting docs/config so PostgreSQL is the only runtime DB path:
  - [`/data/home/tkodippili/Desktop/localTest_context_engine/.env.example`](/data/home/tkodippili/Desktop/localTest_context_engine/.env.example)
  - [`/data/home/tkodippili/Desktop/localTest_context_engine/README.md`](/data/home/tkodippili/Desktop/localTest_context_engine/README.md)
  - [`/data/home/tkodippili/Desktop/localTest_context_engine/docs/deployment.md`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/deployment.md)

## Phase P2 — Production Safety Guardrails
- Add production-only config validation in [`/data/home/tkodippili/Desktop/localTest_context_engine/app/core/config.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/core/config.py):
  - reject default/weak `SECRET_KEY`
  - reject wildcard `ALLOWED_ORIGINS`
  - enforce PostgreSQL runtime requirement (sqlite rejected outside explicit test-only context)
  - reject weak seed admin passwords
  - enforce intentional `LIGHTRAG_DEPLOY_ENABLED` posture
- Split runtime behavior for container targets:
  - production install path in [`/data/home/tkodippili/Desktop/localTest_context_engine/Dockerfile`](/data/home/tkodippili/Desktop/localTest_context_engine/Dockerfile) without `.[dev]` and without `--reload`
  - dev overrides in [`/data/home/tkodippili/Desktop/localTest_context_engine/docker-compose.dev.yml`](/data/home/tkodippili/Desktop/localTest_context_engine/docker-compose.dev.yml)
- Upgrade health/readiness in [`/data/home/tkodippili/Desktop/localTest_context_engine/app/api/routes/health.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/api/routes/health.py):
  - `/health` = process alive
  - `/health/readiness` = dependency checks (DB, Redis when queue-backed, LightRAG reachability/manifest)

## Phase P3 — Bounded Operational APIs + Logging Hygiene
- Add pagination (`limit`/`offset` + max cap) to list endpoints and repository methods:
  - [`/data/home/tkodippili/Desktop/localTest_context_engine/app/api/routes/admin.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/api/routes/admin.py)
  - [`/data/home/tkodippili/Desktop/localTest_context_engine/app/api/routes/jobs.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/api/routes/jobs.py)
  - [`/data/home/tkodippili/Desktop/localTest_context_engine/app/repositories/documents.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/repositories/documents.py)
  - [`/data/home/tkodippili/Desktop/localTest_context_engine/app/repositories/logs.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/repositories/logs.py)
- Add query-log safety controls in settings and logging pipeline:
  - `QUERY_LOG_STORE_TEXT` defaulting to safe behavior in production
  - `QUERY_LOG_RETENTION_DAYS` with retention execution path
  - target modules: [`/data/home/tkodippili/Desktop/localTest_context_engine/app/services/retrieval_service.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/services/retrieval_service.py), [`/data/home/tkodippili/Desktop/localTest_context_engine/app/repositories/logs.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/repositories/logs.py), migrations under [`/data/home/tkodippili/Desktop/localTest_context_engine/migrations/alembic/versions`](/data/home/tkodippili/Desktop/localTest_context_engine/migrations/alembic/versions)

## Documentation and Drift Cleanup (Cross-Phase)
- Update stale brainstorm/docs that still mention removed `/query/*` or outdated `LIGHTRAG_ENABLED` behavior.
- Ensure [`/data/home/tkodippili/Desktop/localTest_context_engine/docs/deployment.md`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/deployment.md) is the canonical source for host-vs-compose variable mapping.
- Keep README concise for first-run path; move advanced LightRAG deploy/provider knobs to dedicated examples and advanced docs.

## Validation and Exit Criteria
- Tests cover:
  - retrieval route contract (`/retrieve` only)
  - startup failure when `DATABASE_URL` is missing/invalid (no sqlite fallback)
  - sqlite rejection outside explicit test-only context
  - production validation failures for unsafe defaults
  - readiness dependency checks
  - paginated admin/job/list responses
  - query-log policy behavior
- Local runbooks verified for:
  - host-first `.env.example`
  - compose startup with compose-specific guidance
  - LightRAG deploy enabled vs disabled behavior clarity
