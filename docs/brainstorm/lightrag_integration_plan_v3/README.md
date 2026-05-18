# Context Engine LightRAG Deployment, Storage, and Concurrency Documentation Package

This package answers the LightRAG deployment and operational questions for the current `context_engine` codebase and gives implementation options that a coding agent can execute after you select a direction.

_Last verified against the codebase: May 2026._

## Files

1. `00_FULL_REPORT.md` — complete senior-engineer report, evidence, recommendations, and junior explanation.
2. `01_CURRENT_FINDINGS.md` — concise map of what is implemented now versus planned or incomplete.
3. `02_IMPLEMENTATION_OPTIONS.md` — selectable implementation options with pros, cons, and when to choose each.
4. `03_CODING_AGENT_PROMPTS.md` — ready-to-paste prompts for a coding agent (hardening-focused where Option 1 core work is already done).
5. `04_ENV_AND_DEPLOYMENT_CHECKLIST.md` — environment variables, Docker services, and verification checklist.
6. `05_CONCURRENCY_AND_FAILURE_MODES.md` — concurrent retrieval, admin upload while users retrieve, and risk controls.

## Current implementation status (summary)

**Done (Option 1 core):** deploy settings in `app/core/config.py` and `.env.example`; `app/lightrag_deploy/` wired through `app/api/routes/lightrag_admin.py`; `GET /lightrag/domains`; CLI/TUI domain screens; `lightrag_domain_id` on upload/query; tests under `tests/test_lightrag_deploy_*` and `tests/test_api.py`.

**Still open:** background or on-demand status refresh from `track_id` → local `READY`; per-domain ingestion lock; explicit per-upload engine selection (`local_backend` vs `lightrag`); domain ACLs if needed.

For the authoritative living list, see `docs/implementation-status.md`.

## Recommended default selection

For a secure local-network deployment with 5–10 users, the recommended starting choice is:

**Option C / Option 1 hybrid:** use one backend PostgreSQL service, one backend Redis service, and keep LightRAG domain storage file-based under `.data/lightrag/domains/<domain_id>/`. Harden the remaining gaps (status polling, ingest lock) before considering shared Postgres/Redis for LightRAG internals.

This is the simplest operational design, easiest to back up, and avoids over-engineering while still supporting multiple LightRAG domain containers.
