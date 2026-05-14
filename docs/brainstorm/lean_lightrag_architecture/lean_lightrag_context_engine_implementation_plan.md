# Lean External LightRAG Integration Plan for `context_engine`

## Purpose

This plan defines how to connect the `context_engine` master codebase to an independently deployed, extremely lean LightRAG service for **context retrieval and graph visualization only**.

The goal is to keep `context_engine` as the main multi-user application and keep LightRAG as an external retrieval/graph engine accessed through a clean HTTP boundary.

---

## 1. Core Architecture

```text
context_engine
  FastAPI app / master codebase
  ├── users/auth/RBAC
  ├── admin-only upload permission
  ├── document mirror registry
  ├── retrieval settings
  ├── query API
  ├── answer/citation pipeline
  ├── query/audit/job logs
  ├── graph visualization proxy routes
  └── LightRAGRemoteAdapter over HTTP

external/lightrag
  lean independently deployed service
  ├── document ingestion endpoint
  ├── context retrieval endpoint
  ├── graph/document-graph endpoints
  ├── optional API shim if upstream LightRAG API needs normalization
  ├── domain manifest/deploy helper
  └── LightRAG storage internals
```

The key rule:

```text
context_engine imports zero LightRAG internals.
context_engine talks to LightRAG only through HTTP.
```

---

## 2. Architectural Reframe

Do **not** rebuild LightRAG as another full application.

Instead:

```text
Do not rebuild LightRAG.
Build a lean LightRAG deployment wrapper + compatibility API for context_engine.
```

That means `external/lightrag` should not become a large custom FastAPI backend unless absolutely required.

Preferred structure:

```text
external/lightrag/
  README.md
  scripts/
    deploy_wizard.sh
  templates/
    docker-compose.lightrag.yml
  data/
    domains.json
  contract/
    openapi.yaml
    examples/
      query_context_response.json
      graph_response.json
```

Optional only if upstream LightRAG does not expose the required API shape:

```text
external/lightrag/shim/
  main.py
  adapters.py
```

The shim should only normalize requests/responses. It must not own users, auth, conversations, dashboards, or app state.

---

## 3. Ownership Boundary

### `context_engine` owns

```text
users
auth
admin permissions
admin-only upload authorization
document mirror records
retrieval settings
query routes
answer/citation pipeline
graph proxy routes
audit/query logs
```

### External LightRAG owns

```text
document ingestion
semantic/context retrieval
graph storage
graph visualization data
vector/graph internals
```

---

## 4. What to Keep Lean

Use `easy-deploy-lightrag` only as a reference for:

```text
domain deployment scripts
domain manifest shape
health checks
graph API ideas
archive-before-delete behavior
Docker Compose deployment pattern
```

Do **not** copy:

```text
full FastAPI server wrapper
LightRAG WebUI
client folder
auth system
conversation system
SQLite user DB
rate limit DB
full vendored LightRAG internals into context_engine/app
```

---

## 5. Storage Decision

Use this storage split:

```text
Postgres:
  context_engine users
  roles
  document mirror records
  retrieval settings/profiles
  jobs
  audit logs
  query logs
  conversations, if enabled

JSON files:
  external/lightrag/data/domains.json only
  generated deployment metadata only

Neo4j:
  not in context_engine
  only inside external/lightrag if LightRAG needs it

Redis:
  optional for context_engine jobs/cache
  useful for upload/index status and background tasks
```

For 5-10 users, Postgres is still the right app database. The reason is not raw scale. The reason is correctness under concurrent reads/writes. JSON is acceptable for a small read-mostly deployment/domain manifest, but not for users, jobs, upload records, presets, and logs.

---

## 6. v1 Scope

Implement only:

```text
1. LightRAGRemoteAdapter
2. LightRAG domain manifest reader
3. admin-only upload forwarding
4. context retrieval through /query/context
5. graph proxy routes
6. retrieval settings from environment + optional JSONB profile
7. deployment wrapper under external/lightrag
8. tests using mocked LightRAG responses
```

Do **not** implement in v1:

```text
PageIndex
local semantic index
hybrid merger
LLM query router
graph editing
LightRAG WebUI
LightRAG auth
conversations inside LightRAG
Neo4j inside context_engine
full retrieval preset CRUD UI
large custom external/lightrag app
```

---

## 7. API Contract First

Before coding implementation details, define:

```text
external/lightrag/contract/openapi.yaml
```

Required endpoints:

```text
GET  /health
POST /documents/upload
GET  /documents/{id}/status
POST /query/context
GET  /graph
GET  /document-graph
```

Optional graph endpoints:

```text
GET /graph/documents/{document_id}
GET /graph/entities
GET /graph/relationships
```

This contract becomes the stable boundary:

```text
external/lightrag must satisfy the contract
context_engine adapter consumes the contract
tests mock the contract
```

---

## 8. Required Request/Response Shapes

### `/query/context` request

```json
{
  "query": "string",
  "domain": "default",
  "mode": "mix",
  "top_k": 10,
  "chunk_top_k": 10,
  "entity_top_k": 10,
  "relationship_top_k": 10,
  "include_sources": true,
  "include_graph_context": true,
  "document_ids": [],
  "filters": {},
  "extra": {}
}
```

### `/query/context` response

```json
{
  "query": "string",
  "domain": "default",
  "results": [
    {
      "id": "chunk-or-graph-id",
      "text": "retrieved context",
      "score": 0.82,
      "document_id": "external-doc-id",
      "source_path": "manual.pdf",
      "page_start": 4,
      "page_end": 5,
      "section_id": "maintenance",
      "section_title": "Maintenance",
      "chunk_id": "chunk-123",
      "entity_ids": [],
      "relationship_ids": [],
      "metadata": {}
    }
  ],
  "debug": {
    "mode": "mix",
    "latency_ms": 321
  }
}
```

### Graph response

```json
{
  "nodes": [
    {
      "id": "entity-1",
      "label": "Alternating Pressure Mattress",
      "type": "entity",
      "metadata": {}
    }
  ],
  "edges": [
    {
      "id": "rel-1",
      "source": "entity-1",
      "target": "entity-2",
      "label": "RELATED_TO",
      "metadata": {}
    }
  ],
  "metadata": {
    "domain": "default",
    "document_id": "external-doc-id",
    "source": "lightrag"
  }
}
```

---

## 9. `context_engine` Changes

### 9.1 Add LightRAG settings

Add to `app/core/config.py` and `.env.example`:

```text
LIGHTRAG_ENABLED=true
LIGHTRAG_DEFAULT_DOMAIN=default
LIGHTRAG_BASE_URL=http://127.0.0.1:9621
LIGHTRAG_API_KEY=
LIGHTRAG_TIMEOUT_SECONDS=120
LIGHTRAG_DOMAINS_MANIFEST_PATH=external/lightrag/data/domains.json

LIGHTRAG_DEFAULT_MODE=mix
LIGHTRAG_DEFAULT_TOP_K=10
LIGHTRAG_DEFAULT_CHUNK_TOP_K=10
LIGHTRAG_DEFAULT_ENTITY_TOP_K=10
LIGHTRAG_DEFAULT_RELATIONSHIP_TOP_K=10
LIGHTRAG_INCLUDE_GRAPH_CONTEXT=true
LIGHTRAG_INCLUDE_SOURCES=true
LIGHTRAG_REQUIRE_HEALTHY=false
```

### 9.2 Add domain manifest reader

Create:

```text
app/integrations/lightrag_domains.py
```

Responsibilities:

```text
read external/lightrag/data/domains.json
return domain name, port, base_url, workspace, status
fallback to LIGHTRAG_BASE_URL when manifest missing
health-check each domain through /health
never require Docker at app runtime
never mutate domains.json during app runtime
```

### 9.3 Add remote adapter

Create:

```text
app/integrations/lightrag_remote_adapter.py
```

Responsibilities:

```text
health check
upload document
retrieve context
get graph
map LightRAG results to Evidence
handle errors
```

Suggested class:

```python
class LightRAGRemoteAdapter:
    async def health(self, *, domain: str | None = None) -> dict:
        ...

    async def retrieve_context(
        self,
        *,
        query: str,
        domain: str | None = None,
        mode: str = "mix",
        top_k: int | None = None,
        chunk_top_k: int | None = None,
        entity_top_k: int | None = None,
        relationship_top_k: int | None = None,
        include_sources: bool = True,
        include_graph_context: bool = True,
        document_ids: list[str] | None = None,
        retrieval_settings: dict | None = None,
    ) -> list[Evidence]:
        ...

    async def upload_document(
        self,
        *,
        domain: str | None,
        filename: str,
        content_type: str,
        content: bytes,
        metadata: dict | None = None,
    ) -> dict:
        ...

    async def get_document_status(
        self,
        *,
        domain: str | None,
        external_document_id: str,
    ) -> dict:
        ...

    async def get_graph(
        self,
        *,
        domain: str | None = None,
        document_id: str | None = None,
        include_entities: bool = True,
        include_relationships: bool = True,
        depth: int | None = None,
    ) -> dict:
        ...
```

Adapter requirements:

```text
use httpx
support timeout
support API key/header
convert remote results into Evidence
preserve chunk/entity/relation metadata
raise typed errors for unavailable service, timeout, invalid JSON, 4xx/5xx
```

---

## 10. Admin Upload Flow

Use one upload path only:

```text
admin uploads file
context_engine checks require_admin
context_engine creates local document mirror row
context_engine forwards file to external LightRAG over HTTP
LightRAG indexes document
context_engine stores external_document_id/domain/status
context_engine records audit log
```

Avoid supporting both HTTP upload and filesystem drop-folder ingestion in v1.

Suggested mirror fields:

```text
documents
  id
  filename
  content_type
  status
  external_engine = "lightrag"
  external_domain
  external_document_id
  external_status
  uploaded_by
  created_at
  updated_at
  metadata_json
```

Normal users:

```text
can query
can inspect citations
can inspect allowed graph/read data
cannot upload
cannot delete
cannot reindex
cannot rebuild graph
```

---

## 11. Query Retrieval Flow

Current target flow:

```text
POST /query/retrieve
  → api/routes/query.py
  → services/retrieval_service.py
  → retrieval/semantic_engine.py or direct retrieval service call
  → integrations/lightrag_remote_adapter.py
  → external LightRAG /query/context
  → Evidence[]
```

Mode mapping for v1:

```text
semantic   -> LightRAG /query/context
hybrid     -> LightRAG /query/context with mode=mix
auto       -> LightRAG /query/context with mode=mix
navigation -> return 400 or map to /query/context until real navigation exists
```

Given this task, LightRAG context retrieval is the production path.

---

## 12. Graph Proxy APIs

Add authenticated routes:

```text
GET /lightrag/graph
GET /lightrag/document-graph
```

Optional:

```text
GET /lightrag/graph/documents/{document_id}
GET /lightrag/graph/entities
GET /lightrag/graph/relationships
```

Add admin/operator routes:

```text
GET /admin/lightrag/domains
GET /admin/lightrag/health
GET /admin/lightrag/graph/raw
```

Rules:

```text
context_engine proxies/normalizes graph data
LightRAG owns graph storage
context_engine does not store nodes/edges in v1
context_engine does not edit graph state in v1
```

---

## 13. Retrieval Settings

Start lean.

### v1 settings sources

```text
1. environment defaults
2. request overrides
3. optional JSONB profile table
```

Avoid a large preset schema with many columns. Use JSONB for flexibility.

Suggested table:

```text
lightrag_retrieval_profiles
  id
  name
  is_default
  settings_json
  created_at
  updated_at
```

Example `settings_json`:

```json
{
  "mode": "mix",
  "top_k": 10,
  "chunk_top_k": 10,
  "entity_top_k": 10,
  "relationship_top_k": 10,
  "include_graph_context": true,
  "include_sources": true
}
```

Merge order:

```text
environment defaults
  → default/admin selected profile
  → per-query overrides, if allowed
```

---

## 14. Deployment Wrapper

Add:

```text
scripts/deploy-lightrag.sh
```

Implementation:

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$ROOT_DIR/external/lightrag/scripts/deploy_wizard.sh" "$@"
```

Supported commands:

```bash
scripts/deploy-lightrag.sh setup
scripts/deploy-lightrag.sh domain add <name> --port <port>
scripts/deploy-lightrag.sh domain list
scripts/deploy-lightrag.sh domain up <name>
scripts/deploy-lightrag.sh domain down <name>
scripts/deploy-lightrag.sh domain status <name>
scripts/deploy-lightrag.sh domain remove <name>
scripts/deploy-lightrag.sh domain recreate <name>
scripts/deploy-lightrag.sh domain regen
```

Deployment script may mutate:

```text
external/lightrag/data/domains.json
```

`context_engine` app runtime should read this file but not write it.

---

## 15. Tests

Add tests in this order:

```text
unit/test_lightrag_remote_adapter.py
unit/test_lightrag_domain_manifest.py
unit/test_retrieval_settings_merge.py
integration/test_query_routes_with_mock_lightrag.py
integration/test_admin_upload_to_mock_lightrag.py
integration/test_graph_proxy_routes.py
integration/test_permissions_admin_upload.py
```

Must test:

```text
LightRAG timeout
LightRAG 500
LightRAG invalid JSON
non-admin upload forbidden
admin upload forwarded
query route maps remote results to Evidence
graph route normalizes nodes/edges
retrieval setting merge order
domain manifest fallback
```

No test should require a live LightRAG service.

---

## 16. Observability

Add structured logs for queries:

```json
{
  "event": "query.completed",
  "user_id": "...",
  "query_id": "...",
  "domain": "default",
  "mode": "semantic",
  "profile": "balanced",
  "evidence_count": 8,
  "lightrag_latency_ms": 430,
  "total_latency_ms": 910
}
```

Add structured logs for uploads:

```json
{
  "event": "document.upload.forwarded",
  "admin_user_id": "...",
  "document_id": "...",
  "external_document_id": "...",
  "domain": "default",
  "status": "indexing"
}
```

---

## 17. Implementation Order

Give the coding agent this order:

```text
1. Add contract files under external/lightrag/contract.
2. Add docs defining the boundary.
3. Add LightRAG settings to context_engine.
4. Add domain manifest reader.
5. Add LightRAGRemoteAdapter with tests.
6. Refactor retrieval path to call LightRAGRemoteAdapter.
7. Add admin upload forwarding.
8. Add graph proxy routes.
9. Add lean retrieval settings merge logic.
10. Add optional JSONB retrieval profile table.
11. Add deploy-lightrag.sh wrapper.
12. Add integration tests with mocked LightRAG.
13. Update README and .env.example.
```

Do not let the coding agent begin by copying the full `easy-deploy-lightrag` repo.

---

## 18. Acceptance Criteria

The task is complete when:

```text
1. context_engine uses external LightRAG for production context retrieval.
2. context_engine does not import LightRAG internals.
3. external/lightrag is lean: deployment + contract + optional shim only.
4. Only admins can upload files.
5. Uploads are forwarded to external LightRAG over HTTP.
6. Regular users can query concurrently.
7. Graph APIs are proxied through context_engine.
8. Retrieval settings are configurable.
9. Postgres stores context_engine runtime state.
10. JSON is used only for LightRAG domain/deployment manifests.
11. Neo4j is not added to context_engine.
12. Tests pass without a live LightRAG service.
13. LightRAG can be updated/redeployed independently from context_engine.
```
