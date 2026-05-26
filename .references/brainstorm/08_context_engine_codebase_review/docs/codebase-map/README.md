# Context Engine Codebase Map Documentation Package

Generated: 2026-05-26

This documentation package is a repo-ready architecture and codebase review set for:

```text
https://github.com/tabesink/context_engine.git
```

It is intended for:

- junior developers
- coding agents
- future maintainers
- frontend integration work
- backend API review
- LightRAG/domain lifecycle work
- production-hardening planning

## How to Use This Package

Place this folder into the repository at:

```text
docs/codebase-map/
```

Recommended reading order:

1. `CODEBASE_INDEX.md`
2. `ARCHITECTURE.md`
3. `RAG_PIPELINE.md`
4. `API_MAP.md`
5. `DATABASE_AND_STORAGE_SCHEMA.md`
6. `CONFIGURATION_AND_DEPLOYMENT.md`
7. `ARCHITECTURE_REVIEW.md`
8. `REFACTORING_ROADMAP.md`
9. `CODING_AGENT_GUIDE.md`
10. `ADRS_TO_WRITE.md`

## Important Review Position

This review does **not** recommend rewriting the system.

The current architecture is moving in a good direction:

```text
FastAPI backend
  → PostgreSQL app state
  → Redis/RQ background jobs
  → remote LightRAG semantic retrieval
  → local document navigation retrieval
  → single /retrieve evidence API
```

The main recommendation is to make the architecture easier to understand, safer to operate, and clearer for frontend integration.

## Top Recommendations

1. Document the shared-corpus access model as an intentional architecture decision.
2. Resolve the CLI/TUI support contradiction in project docs.
3. Pin LightRAG container images in staging/production.
4. Add a small `RetrievalAccessPolicy` before deeper frontend integration.
5. Keep `/retrieve` as the single evidence/retrieval API.
