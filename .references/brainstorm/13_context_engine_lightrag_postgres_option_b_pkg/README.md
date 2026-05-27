# Context Engine LightRAG Postgres Option B Implementation Package

This package is a handoff for a junior developer or coding agent to implement **Option B: Postgres-backed LightRAG domains with explicit database provisioning**.

## Problem being fixed

The current failure:

```text
postgres-1 | FATAL: password authentication failed for user "lightrag"
postgres-1 | DETAIL: Role "lightrag" does not exist.
```

means the managed LightRAG container can reach Postgres, but its generated runtime environment points at a database role that has not been created. This is different from the earlier API-to-LightRAG DNS problem.

## Target outcome

For every managed LightRAG domain, Context Engine must ensure:

1. A domain-specific Postgres role exists.
2. A domain-specific Postgres database exists.
3. Required extensions are available in that database: `vector` and `AGE` where supported by the image.
4. The generated `domain.env` uses the same database/user/password that were provisioned.
5. `repair` can re-run provisioning safely and regenerate/recreate the LightRAG container.

## Contents

- `docs/00_diagnosis.md` — root-cause analysis.
- `docs/01_target_architecture.md` — target architecture for Postgres-backed LightRAG domains.
- `docs/02_pr_implementation_plan.md` — PR-sized implementation plan.
- `docs/03_repair_runbook.md` — immediate local repair commands.
- `docs/04_acceptance_tests.md` — acceptance and regression tests.
- `docs/05_coding_agent_prompt.md` — paste-ready prompt for coding agents.
- `patches/` — implementation skeletons and patch guidance.
- `scripts/diagnose_lightrag_postgres.sh` — diagnostic helper.
- `sql/local_repair_create_lightrag_role.sql` — temporary triage SQL.

## Important implementation decision

Do **not** silently fix this by pointing LightRAG at the app’s `context_engine` database/user unless you intentionally choose a shared-runtime mode. The cleaner Option B is per-domain provisioning:

```text
Context Engine app DB:
  database: context_engine
  user: context_engine

LightRAG fatigue domain DB:
  database: lightrag_fatigue
  user: lightrag_fatigue
```

This preserves a clear boundary between app state and LightRAG index state.
