# Context Engine Lean Cleanup Package

Generated: 2026-05-28
Repository reviewed: `https://github.com/tabesink/context_engine.git`

This package turns the lean-codebase audit into implementation-ready documentation for a junior developer and coding agent.

## Important review limitation

This was a static review of the public GitHub repository through the GitHub web UI. The execution environment could not clone or run the repository because DNS resolution for `github.com` failed in the local container. Treat this package as a strong cleanup planning artifact, then verify each finding against the current checked-out branch before changing code.

## Recommended usage

1. Start with `LEAN_CODEBASE_CLEANUP_REVIEW.md`.
2. Use `LIGHTRAG_DOMAIN_LIFECYCLE_AUDIT.md` before touching domain lifecycle APIs.
3. Use `STATE_OWNERSHIP_MATRIX.md` before touching document/domain/job status behavior.
4. Assign tasks from `CODING_AGENT_IMPLEMENTATION_PLAN.md` one at a time.
5. Use `CLEANUP_ROADMAP.md` as the phase sequence.
6. Keep `PRESERVE_LIST.md` visible so cleanup does not remove important product capability.

## Package contents

| File | Purpose |
|---|---|
| `LEAN_CODEBASE_CLEANUP_REVIEW.md` | Main findings, severity, and top cleanup priorities. |
| `CODEBASE_INDEX.md` | Repo map, ownership notes, and reading order. |
| `API_SURFACE_OVERLAP_MAP.md` | Route/API overlap map focused on admin/domain/document/status surfaces. |
| `LIGHTRAG_DOMAIN_LIFECYCLE_AUDIT.md` | Deep audit of `up/down/recreate/repair/regenerate/archive/purge`. |
| `STATE_OWNERSHIP_MATRIX.md` | Domain/document/job/status source-of-truth recommendations. |
| `CLEANUP_ROADMAP.md` | Phased cleanup plan. |
| `CODING_AGENT_IMPLEMENTATION_PLAN.md` | Small, implementation-ready tasks with acceptance criteria. |
| `JUNIOR_DEVELOPER_GUIDE.md` | Navigation guide and safe/risky zones. |
| `PRESERVE_LIST.md` | Architecture choices that should not be removed. |
| `GITHUB_REVIEW_EVIDENCE.md` | Evidence gathered from repository structure and source files. |

## Cleanup posture

The objective is not to make the repo tiny. The objective is to make it easier to reason about while preserving:

- multi-user auth boundaries
- admin-only write/ingestion boundaries
- LightRAG HTTP/runtime boundary
- document registry and job safety
- evidence/citation contract
- Docker/local deployment capability
- existing tests as a regression safety net
