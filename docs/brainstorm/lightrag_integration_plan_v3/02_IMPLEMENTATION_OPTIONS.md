# Recommended Implementation Options

This file gives selectable implementation options. A coding agent should not implement all of them. Choose one primary option first.

---

## Option 1 — Recommended: File-Based LightRAG Domains + One Backend Postgres + One Backend Redis

### Summary

Use the existing backend PostgreSQL and Redis exactly as they are. Deploy LightRAG domains as separate LightRAG containers with per-domain file storage under:

```text
.data/lightrag/domains/<domain_id>/
```

### Architecture

```text
Context Engine API
  ├── PostgreSQL: app tables
  ├── Redis: app jobs
  └── LightRAG domains over HTTP
        ├── manuals -> .data/lightrag/domains/manuals/rag_storage
        └── catalog -> .data/lightrag/domains/catalog/rag_storage
```

### Why choose this

Choose this if you want:

- simplest deployment;
- fewer services;
- easy backup;
- enough power for 5–10 users;
- clean per-domain isolation;
- junior-developer maintainability.

### Pros

- Matches the direction of `app/lightrag_deploy/`.
- Does not require separate LightRAG Postgres/Redis.
- Keeps backend database clean.
- Each domain has a simple folder to inspect and back up.
- Easy to explain to junior developers.

### Cons

- Must verify LightRAG file-storage behavior under read/write concurrency.
- May not scale to very large corpora.
- Requires ingestion lock per domain.

### Required work

**Done (May 2026):**

1. LightRAG deployment settings in `app/core/config.py` and `.env.example`.
2. `app/lightrag_deploy/` wired through `app/api/routes/lightrag_admin.py`.
3. `GET /lightrag/domains` for authenticated users.
4. TUI screens and CLI services for domain lifecycle.
5. `lightrag_domain_id` on admin upload and query payloads.

**Remaining hardening:**

1. Explicit per-upload engine selection: `local_backend` vs `lightrag` (not only global `LIGHTRAG_ENABLED`).
2. Remote LightRAG status refresh (worker or `POST /admin/documents/{id}/refresh-lightrag-status`).
3. Redis lock for one ingestion per domain.
4. Optional domain ACLs if multi-tenant isolation is required.

### Acceptance criteria

```text
[x] Admin can create a domain named manuals.
[x] Domain folders are created.
[x] Domain env file is generated.
[x] Domain compose file is generated.
[x] Admin can start/stop domain (up/down/recreate via API/TUI).
[x] Domain manifest is written.
[x] Normal users can list queryable domains.
[x] Admin can upload document to manuals (lightrag_domain_id).
[x] Upload stores local document row with LightRAG track_id.
[ ] Status refresh marks document READY when remote indexing completes.
[ ] Users can query manuals while another document is indexing (verify at runtime).
[ ] Same-domain concurrent uploads are blocked or queued.
```

---

## Option 2 — Single Global LightRAG Server Only

### Summary

Do not implement multi-domain deployment yet. Use one external LightRAG server and one `LIGHTRAG_BASE_URL`.

### Why choose this

Choose this if you need to validate LightRAG quickly before building domain lifecycle management.

### Pros

- Fastest path to testing remote LightRAG retrieval.
- Minimal code change.
- Good proof-of-concept.

### Cons

- Not enough for long-term multi-domain admin management.
- All users share one LightRAG corpus.
- Harder to isolate documentation sets.
- Does not solve your target domain-deployment design.

### Required work

1. Set `LIGHTRAG_ENABLED=true`.
2. Start a LightRAG server manually.
3. Set `LIGHTRAG_BASE_URL`.
4. Verify `/query/retrieve` and `/graphs` work.
5. Add minimal status checks.

### Acceptance criteria

```text
[ ] Backend can retrieve from remote LightRAG.
[ ] Backend can upload to remote LightRAG.
[ ] Graph endpoints proxy successfully.
[ ] Users can query shared corpus.
```

---

## Option 3 — Shared PostgreSQL and Redis for Backend + LightRAG

### Summary

Use one PostgreSQL container and one Redis container for both Context Engine and LightRAG, but isolate by database/schema/key prefix.

### Why choose this

Choose only if LightRAG is intentionally configured to use PostgreSQL and Redis as storage backends.

### Pros

- Fewer infrastructure containers than fully separate DB/Redis per LightRAG.
- Centralized backup for DB-backed state.
- Better scaling path than Python JSON embeddings.

### Cons

- More complex configuration.
- Namespace collision risk.
- Requires confidence in LightRAG external-storage configuration.
- More difficult for junior developers than file-based domain storage.

### Required work

1. Confirm official LightRAG env variables for Postgres/Redis storage.
2. Add LightRAG database/schema creation logic.
3. Add Redis DB index or key prefix isolation.
4. Update generated domain env files.
5. Add backup/restore docs.
6. Add tests that ensure no shared table/key collisions.

### Recommended isolation

```text
PostgreSQL:
- context_engine database for backend
- lightrag_<domain_id> database for each LightRAG domain

Redis:
- DB 0 or prefix ce:* for Context Engine jobs
- DB 1 or prefix lr:<domain_id>:* for LightRAG
```

---

## Option 4 — Separate PostgreSQL/Redis per LightRAG Deployment

### Summary

Deploy separate Postgres and Redis services for LightRAG, separate from the Context Engine backend services.

### Why choose this

Choose if you need strong isolation or expect LightRAG to become operationally heavy.

### Pros

- Strong isolation.
- Easier to separate failures.
- Easier to migrate LightRAG independently later.

### Cons

- More containers.
- More credentials.
- More backups.
- More operational burden.
- Overkill for 5–10 local-network users.

### Recommendation

Not recommended for first implementation.

---

## Option 5 — Remove Remote LightRAG for Now and Improve Local Backend RAG

### Summary

Do not run LightRAG at all. Improve the local backend semantic system by replacing JSON embeddings with pgvector and real embeddings.

### Why choose this

Choose this if the immediate goal is simple reliable document retrieval, not LightRAG graph features.

### Pros

- One app, one database, one Redis.
- Very simple deployment.
- Easier to test.
- No external LightRAG runtime uncertainty.

### Cons

- Not LightRAG.
- No LightRAG graph capabilities.
- Does not match your long-term domain-container plan.

### Recommendation

Good fallback option, but not the best match for your stated direction.

---

## Decision matrix

| Option | Simplicity | Multi-domain | Good for 5–10 users | Backup ease | Future scale | Recommendation |
|---|---:|---:|---:|---:|---:|---|
| Option 1: file-based LightRAG domains | High | High | High | High | Medium | Best first choice |
| Option 2: single global LightRAG | Very high | Low | Medium | Medium | Low | Proof-of-concept only |
| Option 3: shared PG/Redis | Medium | High | High | Medium | High | Later, if needed |
| Option 4: separate PG/Redis | Low | High | High | Low | High | Overkill now |
| Option 5: local backend RAG only | Very high | Medium | High | High | Medium | Fallback |
