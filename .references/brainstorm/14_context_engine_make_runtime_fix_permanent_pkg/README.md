# Context Engine — Make LightRAG Runtime Fix Permanent

Date: 2026-05-27

## Goal

Convert the current local runtime workaround into a permanent, low-entropy implementation:

- LightRAG managed domains using PostgreSQL must provision their database role/database/extensions before startup.
- Legacy containers that still use `POSTGRES_USER=lightrag` must be intentionally supported through a compatibility mode, not manual SQL drift.
- Generated `domain.env` files must be deterministic and must never point LightRAG at a non-existent Postgres role.
- Managed LightRAG containers must have reliable tokenizer/tiktoken startup in Docker, without external DNS dependency during container boot.
- Admin repair must regenerate env, provision Postgres, recreate the domain, and return actionable diagnostics.

## Why this is needed

The temporary fix created compatibility database objects manually:

- role: `lightrag`
- database: `lightrag`
- privileges
- `vector` extension

That made the legacy `lightrag_fatigue` container healthy, but it is not permanent because a clean `docker compose down -v`, fresh developer machine, CI run, or new managed domain can recreate the same failure.

## Package contents

- `docs/00_current_review.md` — current codebase review based on the modified repo.
- `docs/01_target_architecture.md` — permanent storage and container-start architecture.
- `docs/02_implementation_plan.md` — PR-sized phases for a junior dev/coding agent.
- `docs/03_repair_runbook.md` — commands to verify and repair current stack.
- `docs/04_acceptance_tests.md` — concrete test matrix.
- `docs/05_coding_agent_prompt.md` — ready-to-paste prompt.
- `patches/` — implementation skeletons.
- `scripts/diagnose_lightrag_runtime.sh` — local diagnostic script.
- `sql/bootstrap_lightrag_compat.sql` — legacy compatibility bootstrap SQL.
- `tests/` — test skeletons.

## Important target decision

Use **Postgres-backed LightRAG** permanently, but with explicit provisioning:

```text
Context Engine app DB/user:
  context_engine / context_engine

Managed domain DB/user:
  lightrag_<domain> / lightrag_<domain>

Legacy compatibility DB/user:
  lightrag / lightrag
```

Do not rely on manual SQL fixes.
