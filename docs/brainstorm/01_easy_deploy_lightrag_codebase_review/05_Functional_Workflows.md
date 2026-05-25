# 5. Functional Workflow Walkthroughs

## Workflow A: Start the System Locally

Likely operator path:

```text
1. Install project dependencies.
2. Configure `.env` / runtime settings.
3. Run CLI setup or domain setup.
4. Start Docker Compose services.
5. Start backend server.
6. Start Next.js client, if using custom UI.
7. Open client and log in with bootstrap admin.
```

Code surfaces involved:

| Step | File / Function |
|---|---|
| Configure backend defaults | `src/server/config/settings.py` / `get_settings()` |
| Generate runtime env/manifest/compose | `cli/main.py` / `_ensure_runtime_files()`, `_write_compose()` |
| Add domain | `cli/main.py` / `_add_domain()`, `_write_domain_env()` |
| Start Compose | `cli/main.py` / `_run_compose()` |
| Start backend | `src/server/app/main.py` / `main()` |
| Bootstrap admin | `src/server/auth/security.py` / `bootstrap_admin()` |
| Start frontend | `client/` Next.js project |

## Workflow B: Deploy a New Domain Knowledge Base

```text
Operator
   │
   ▼
lightrag-cli domain add <domain> --port <port>
   │
   ├── validate domain id
   ├── choose or validate port
   ├── update data/domains.json
   ├── create data/domains/<domain>/
   │      ├── .env
   │      ├── inputs/
   │      ├── rag_storage/
   │      └── artifacts/
   ├── regenerate docker-compose.domains.yml
   └── optionally start/recreate service
```

Key code:

| Function | Role |
|---|---|
| `_validate_domain_id()` | Ensures safe domain name. |
| `_next_available_port()` | Picks an unused domain port. |
| `_write_domain_env()` | Writes per-domain env/config. |
| `_add_domain()` | Main domain creation logic. |
| `_compose_domain()` | Creates Compose service block. |
| `_write_compose()` | Writes full Compose file. |

## Workflow C: Add Documents and Index Them

The custom backend under `src/server` did not show a dedicated document upload/index route. Document ingestion appears to be handled by native LightRAG APIs/UI and/or files placed into each domain input folder.

Likely flow:

```text
Source documents
   │
   ▼
data/domains/<domain>/inputs/
   │  mounted to
   ▼
LightRAG container /app/data/inputs
   │
   ▼
Native LightRAG document/index APIs
   │
   ├── parses documents
   ├── may use Docling structural chunking
   ├── writes artifacts
   ├── writes vector/KV/doc status to PostgreSQL
   ├── writes graph data to Neo4j
   └── may use Redis for cache/storage
```

Relevant files:

| File | Relevance |
|---|---|
| `src/lightrag/api/routers/document_routes.py` | Native LightRAG document route surface. Inspect locally for exact endpoints. |
| `src/lightrag/structural_chunking.py` | Docling structural artifact creation and section/block extraction. |
| `Dockerfile.lightrag-local` | Installs Docling and copies customized `src/lightrag`. |
| `docker-compose.domains.yml` | Mounts per-domain `inputs`, `rag_storage`, and `artifacts`. |

## Workflow D: Query / Retrieve Context Through Custom Backend

```text
User in Next.js client
   │
   ▼
POST /api/conversations/{conversation_id}/messages
   │
   ▼
src/server/conversations/router.py / post_message()
   │
   ▼
src/server/conversations/service.py / post_message_stream()
   │
   ▼
src/server/context/stream_service.py / run_chat_turn()
   │
   ├── save user message
   ├── save assistant placeholder
   ├── apply rate limit
   ├── retrieve context unless selected context provided
   │       │
   │       ▼
   │   POST {LightRAG}/query/context
   │   src/server/context/retrieval_service.py / retrieve_context()
   │
   ├── build/source-tree context event
   ├── save source tree snapshot
   ├── call LightRAG answer endpoint
   │       │
   │       ▼
   │   POST {LightRAG}/query
   │   src/server/context/stream_service.py / query_lightrag()
   │
   ├── stream token events
   ├── save completed assistant message
   └── yield done event
```

The backend supports per-request LightRAG port override through `RetrievalSettings.lightrag_port`. When provided, `_lightrag_base_url()` uses:

```text
http://127.0.0.1:{lightrag_port}
```

Otherwise it uses `settings.lightrag_base_url`.

## Workflow E: Graph Visualization and Editing

```text
Next.js graph UI
   │
   ▼
client/src/api/lightrag.ts
   │
   ▼
Custom backend /api/lightrag/domains/{port}/graph...
   │
   ▼
src/server/lightrag/router.py
   │
   ▼
src/server/lightrag/graph_proxy.py
   │
   ├── validate selected port against discovered domains
   ├── forward request to LightRAG domain
   └── return JSON response
```

Frontend graph surfaces:

| File | Purpose |
|---|---|
| `client/src/features/graph/GraphViewer.tsx` | Main graph visualization component. |
| `client/src/api/lightrag.ts` | Graph API client functions. |
| `client/src/stores/graph.ts` | Zustand/graphology/sigma graph state. |
| `client/src/stores/lightrag-domain-store.ts` | Selected domain/port state. |

Write actions:

| Backend Route | Permission |
|---|---|
| `POST /api/lightrag/domains/{port}/graph/entity/edit` | Admin or `can_write` |
| `POST /api/lightrag/domains/{port}/graph/relation/edit` | Admin or `can_write` |

## Workflow F: Stop or Delete a Domain

```text
Operator
   │
   ▼
lightrag-cli domain remove <domain>
   │
   ├── stop Docker service
   ├── remove domain entry from manifest
   ├── move domain folder to data/domains/_deleted/<domain>-<timestamp>
   ├── remove active folder
   └── regenerate compose file
```

Key file/function:

- `cli/main.py` / `_remove_domain()`

Safety note: this is an operationally dangerous path. It intentionally removes the active domain folder after archiving. Operators should confirm archive behavior locally before using this on important corpora.

## Workflow G: Admin User Management

```text
Admin logs in
   │
   ▼
JWT cookie set by /api/v1/auth/login
   │
   ▼
Admin uses settings/users page or API
   │
   ▼
/api/v1/admin/users routes
   │
   ├── list users
   ├── create user
   ├── update role/can_write
   ├── reset password
   ├── delete user
   └── view pending settings count
```

Important safeguards:

- Admin cannot delete self.
- Admin cannot remove own admin role/access through update route.
- User changes are audit logged.

## Workflow H: Backend Domain Discovery

```text
FastAPI startup
   │
   ▼
src/server/app/main.py / create_app()
   │
   ▼
discover_domains(settings)
   │
   ├── read data/domains.json
   ├── health-check each domain base URL
   ├── return healthy domains if any
   └── otherwise return fallback default domain from settings.lightrag_base_url
```

Important implication: if domain containers are not healthy at backend startup, the backend may fall back to only the default domain. Confirm whether domains refresh dynamically in the UI or require backend restart/reload.
