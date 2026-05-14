# Coding Agent Prompt: Lean External LightRAG Boundary for `context_engine`

## Role

You are a senior software architect and implementation-focused coding agent. You are modifying the `context_engine` master codebase.

Your goal is to connect `context_engine` to an independently deployed, extremely lean LightRAG service for **context retrieval and graph visualization only**.

Do not rewrite the entire system. Do not copy LightRAG internals into `context_engine/app`.

---

## Core Objective

Add a clean external LightRAG service boundary to `context_engine`.

```text
context_engine = master multi-user app
external/lightrag = lean retrieval + graph service
```

Communication must happen through HTTP only.

---

## Hard Rules

Do not:

```text
copy full easy-deploy-lightrag server into context_engine
copy LightRAG WebUI
copy client folder
copy auth/conversation/SQLite app control plane
import LightRAG internals from context_engine/app
add Neo4j to context_engine
store graph nodes/edges in context_engine v1
implement PageIndex in this task
implement local semantic index in this task
implement LLM query router in this task
```

Do:

```text
add LightRAGRemoteAdapter
add domain manifest reader
add admin-only upload forwarding
add context retrieval via /query/context
add graph proxy routes
add retrieval settings from env + optional JSONB profile
add deploy wrapper under scripts/deploy-lightrag.sh
add contract files under external/lightrag/contract
add tests with mocked LightRAG responses
```

---

## Required Architecture

```text
context_engine
  owns:
    users
    auth
    admin permissions
    admin-only upload authorization
    document mirror records
    retrieval settings
    query routes
    graph proxy routes
    audit/query logs

external/lightrag
  owns:
    document ingestion
    context retrieval
    graph storage
    graph visualization data
    vector/graph internals
```

---

## Step 1: Add Contract Files

Create:

```text
external/lightrag/contract/openapi.yaml
external/lightrag/contract/examples/query_context_response.json
external/lightrag/contract/examples/graph_response.json
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

Optional:

```text
GET /graph/documents/{document_id}
GET /graph/entities
GET /graph/relationships
```

---

## Step 2: Add LightRAG Settings

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

---

## Step 3: Add Domain Manifest Reader

Create:

```text
app/integrations/lightrag_domains.py
```

It should:

```text
read external/lightrag/data/domains.json
return domain name, port, base_url, workspace, status
fallback to LIGHTRAG_BASE_URL when manifest missing
health-check each domain through /health
never require Docker at app runtime
never write domains.json during app runtime
```

---

## Step 4: Add LightRAGRemoteAdapter

Create:

```text
app/integrations/lightrag_remote_adapter.py
```

Suggested methods:

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
convert LightRAG results into Evidence
preserve chunk/entity/relation metadata
raise typed errors for service unavailable, timeout, invalid JSON, 4xx/5xx
```

---

## Step 5: Refactor Retrieval Flow

Target flow:

```text
POST /query/retrieve
  → api/routes/query.py
  → services/retrieval_service.py
  → LightRAGRemoteAdapter.retrieve_context()
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

---

## Step 6: Admin-Only Upload Forwarding

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

Normal users must receive 403 on upload/delete/reindex routes.

---

## Step 7: Add Graph Proxy Routes

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
proxy/normalize graph data only
do not store graph nodes/edges in context_engine v1
do not implement graph editing in v1
```

---

## Step 8: Add Retrieval Settings

Start lean.

Merge order:

```text
environment defaults
  → optional JSONB profile
  → per-query overrides, if allowed
```

Optional table:

```text
lightrag_retrieval_profiles
  id
  name
  is_default
  settings_json
  created_at
  updated_at
```

Use JSONB to avoid schema churn as LightRAG settings evolve.

---

## Step 9: Add Deployment Wrapper

Create:

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

Also create:

```text
external/lightrag/scripts/deploy_wizard.sh
external/lightrag/data/domains.json
external/lightrag/templates/docker-compose.lightrag.yml
```

---

## Step 10: Tests

Add tests:

```text
unit/test_lightrag_remote_adapter.py
unit/test_lightrag_domain_manifest.py
unit/test_retrieval_settings_merge.py
integration/test_query_routes_with_mock_lightrag.py
integration/test_admin_upload_to_mock_lightrag.py
integration/test_graph_proxy_routes.py
integration/test_permissions_admin_upload.py
```

No test should require a real LightRAG service.

Test:

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

---

## Acceptance Criteria

The implementation is complete when:

```text
1. context_engine uses external LightRAG for production context retrieval.
2. context_engine imports no LightRAG internals.
3. external/lightrag remains lean: deployment + contract + optional shim only.
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
