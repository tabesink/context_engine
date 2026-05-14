# Architecture Decisions: Lean External LightRAG Boundary

## ADR-001: `context_engine` remains the master app

### Decision

`context_engine` owns users, auth, admin permissions, document mirror records, retrieval settings, query routes, graph proxy routes, and audit/query logs.

### Rationale

This keeps all multi-user application concerns in one place and avoids duplicating auth or app state inside LightRAG.

### Consequence

External LightRAG should not have its own user system, conversation system, dashboard, or app-control database for this integration.

---

## ADR-002: LightRAG is external and accessed through HTTP only

### Decision

`context_engine` communicates with LightRAG through `LightRAGRemoteAdapter` over HTTP.

### Rationale

This allows LightRAG to be updated, rebuilt, or redeployed independently.

### Consequence

`context_engine` must not import LightRAG internals or vendor the full LightRAG source into `app/`.

---

## ADR-003: `external/lightrag` should be deployment + contract + optional shim

### Decision

`external/lightrag` should contain deployment scripts, domain manifest, contract files, examples, and optionally a tiny API shim.

### Rationale

A full rebuilt backend under `external/lightrag` would duplicate `context_engine` and increase entropy.

### Consequence

Create `external/lightrag/app` only if upstream LightRAG cannot satisfy the needed contract directly.

---

## ADR-004: Use Postgres for `context_engine` runtime state

### Decision

Use Postgres for users, roles, document mirror records, retrieval profiles, jobs, audit logs, and query logs.

### Rationale

Even for 5-10 users, concurrent writes require a real transactional database.

### Consequence

JSON files are not used for app runtime state.

---

## ADR-005: Use JSON only for LightRAG deployment manifests

### Decision

Use `external/lightrag/data/domains.json` only for domain/deployment metadata.

### Rationale

A read-mostly manifest is appropriate for JSON. Mutable app state is not.

### Consequence

Deployment scripts may write `domains.json`; `context_engine` runtime should only read it.

---

## ADR-006: Do not add Neo4j to `context_engine`

### Decision

Neo4j, if needed, belongs only inside the external LightRAG deployment.

### Rationale

`context_engine` should not own graph storage. It should proxy/normalize graph visualization data.

### Consequence

No graph nodes/edges are stored in `context_engine` v1.

---

## ADR-007: Admin upload uses one HTTP forwarding path

### Decision

Admin uploads go through `context_engine`, which forwards the file to LightRAG over HTTP.

### Rationale

One ingestion path is easier to reason about, test, secure, and document.

### Consequence

Do not support both HTTP upload and filesystem drop-folder ingestion in v1.

---

## ADR-008: Retrieval settings start as env + JSONB profile

### Decision

Start with environment defaults and optional JSONB retrieval profiles.

### Rationale

LightRAG settings may evolve. JSONB avoids frequent schema migrations.

### Consequence

Do not create a large multi-column retrieval preset schema in v1 unless product requirements demand it.

---

## ADR-009: Graph APIs are proxy/normalization APIs

### Decision

`context_engine` exposes graph visualization APIs by proxying LightRAG graph endpoints.

### Rationale

Frontend users should not call LightRAG directly, but graph ownership remains with LightRAG.

### Consequence

Graph editing, graph caching, and graph persistence in `context_engine` are out of scope for v1.

---

## ADR-010: Contract-first integration

### Decision

Create `external/lightrag/contract/openapi.yaml` before implementing adapter details.

### Rationale

A stable contract keeps both sides independently testable.

### Consequence

`context_engine` tests should mock the LightRAG contract and not require a live LightRAG service.
