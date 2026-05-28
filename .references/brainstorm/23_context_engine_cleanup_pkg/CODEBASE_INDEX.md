# Codebase Index and Reading Order

## Repository map

```text
context_engine/
├── app/
│   ├── api/
│   │   └── routes/
│   ├── core/
│   ├── document_processing/
│   ├── domain/
│   ├── integrations/
│   ├── lightrag_deploy/
│   ├── retrieval/
│   ├── schemas/
│   ├── services/
│   ├── storage/
│   ├── workers/
│   └── main.py
├── cli/
├── client/
│   └── src/
│       ├── api/
│       ├── app/
│       ├── components/
│       ├── features/
│       ├── hooks/
│       ├── lib/
│       ├── stores/
│       ├── types/
│       └── utils/
├── docker/
├── docs/
├── external/lightrag/
├── migrations/
├── scripts/
├── tests/
├── .env.example
├── .env.lightrag-deploy.example
└── .env.lightrag-provider.example
```

## Ownership notes

### `app/api/routes/`
Owns HTTP API shape only. Route handlers should not own heavy domain lifecycle orchestration, document status composition, or repeated repository plumbing.

### `app/services/`
Owns use-case logic. This folder currently has many focused services, but the number of status/lifecycle/retrieval-adjacent services makes ownership harder to infer. Avoid adding another service until existing overlaps are mapped.

### `app/lightrag_deploy/`
Owns LightRAG runtime deployment mechanics: manifest, Docker, Compose, paths, settings, and domain runtime orchestration. This folder is powerful but currently concentrates too many responsibilities in `service.py`.

### `app/storage/`
Owns database access, tables, sessions, and repositories. Routes and UI should not know persistence details directly.

### `app/workers/`
Owns async/background execution and polling. Status-poller behavior must not drift from API status semantics.

### `client/src/api/`
Should own backend API calls. Avoid duplicating fetch logic in components.

### `client/src/hooks/`
Should own reusable polling and state synchronization hooks. Avoid one-off polling inside multiple components.

### `client/src/components/` and `client/src/features/`
Should own UI composition. Components should not know LightRAG/Docker internals.

## Recommended reading order for cleanup

1. `README.md` — runtime/deployment assumptions.
2. `app/main.py` — application wiring.
3. `app/api/routes/lightrag_admin.py` — domain lifecycle surface.
4. `app/lightrag_deploy/service.py` — domain lifecycle implementation.
5. `app/services/lightrag_domain_lifecycle_service.py` — persisted lifecycle state wrapper.
6. `app/workers/status_poller.py` — domain health/status background behavior.
7. `app/api/routes/documents.py` — document/status/source navigation API shape.
8. `app/api/routes/jobs.py` — job status API shape.
9. `app/services/processing_status_service.py` and `processing_status_cache.py` — status composition/cache behavior.
10. `app/services/retrieval_service.py`, `workspace_context_service.py`, `workspace_tree_service.py` — evidence/context surfaces.
11. `client/src/api/`, `client/src/hooks/`, and relevant pages/components — frontend contract and polling behavior.
12. `tests/` — current safety net before refactors.

## High-probability cleanup artifacts to verify

These appear in repository listings and should be checked for VCS cleanup:

- `.data/uploads/`
- `.vs/`
- `context_engine.egg-info/`
- `__pycache__/`
- `client/tsconfig.tsbuildinfo`
- `migrations/2popups.png`

If committed, remove them from Git after confirming they are not intentionally versioned, and update `.gitignore`.
