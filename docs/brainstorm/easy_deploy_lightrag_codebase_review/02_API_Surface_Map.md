# 2. API Surface Map

This file maps the visible custom FastAPI backend under `src/server`. It does not fully enumerate all upstream/native LightRAG API routes under `src/lightrag/api/routers/`, although the relevant router files are listed near the end.

## 2.1 Application Startup

| Area | Evidence |
|---|---|
| App factory | `src/server/app/main.py`, function `create_app(settings: Settings | None = None) -> FastAPI` |
| Runtime command | `src/server/app/main.py`, function `main()` uses `uvicorn.run("server.app.main:create_app", factory=True)` |
| Middleware | `src/server/app/main.py` installs CORS and request ID middleware from `src/server/app/middleware.py` |
| Startup actions | `bootstrap_admin(settings)` and `application.state.lightrag_domains = discover_domains(settings)` |
| Routers included | `auth_router`, `users_admin_router`, `conversations_router`, `lightrag_router` |

## 2.2 Health API

| Route | Method | File / Function | Purpose | Auth |
|---|---:|---|---|---|
| `/health` | GET | `src/server/app/main.py` / inner `health()` | Returns service status, environment, `/api` prefix, configured LightRAG base URL. | Public |

Response model: `HealthResponse` with fields:

- `service`
- `status`
- `environment`
- `api_prefix`
- `lightrag_base_url`

## 2.3 Auth API

Router: `src/server/auth/router.py`  
Prefix: `/api/v1/auth`

| Route | Method | Function | Purpose | Auth |
|---|---:|---|---|---|
| `/api/v1/auth/login` | POST | `login()` | Validates username/password, updates last login, logs audit, sets JWT cookie. | Public |
| `/api/v1/auth/logout` | POST | `logout()` | Logs optional logout audit and deletes auth cookie. | Optional user |
| `/api/v1/auth/me` | GET | `me()` | Returns current authenticated user. | Required |
| `/api/v1/auth/change-password` | POST | `change_password()` | Verifies current password, hashes/stores new password, logs audit. | Required |

Key supporting files:

| File | Responsibility |
|---|---|
| `src/server/auth/security.py` | Password hashing/verification, admin bootstrap, JWT creation, auth cookie helpers. |
| `src/server/auth/deps.py` | `optional_user`, `current_user`, `admin_user` dependency functions. |
| `src/server/users/schemas.py` | User response/request schemas. |

Auth details:

- Password hashing uses bcrypt in `hash_password()`.
- JWT tokens are created by `create_token()` with `sub`, `username`, `role`, `can_write`, `iat`, and `exp` claims.
- Auth cookie is HTTP-only and configurable via `BACKEND_AUTH_COOKIE_*` settings.

## 2.4 Admin User API

Router: `src/server/users/router_admin.py`  
Prefix: `/api/v1/admin/users`

| Route | Method | Function | Purpose | Auth |
|---|---:|---|---|---|
| `/api/v1/admin/users` | GET | `list_users()` | Lists users. | Admin |
| `/api/v1/admin/users` | POST | `create_user()` | Creates a user and logs audit. | Admin |
| `/api/v1/admin/users/{user_id}` | PATCH | `update_user()` | Updates role/can_write/settings flags. Prevents self role/access downgrade. | Admin |
| `/api/v1/admin/users/{user_id}` | DELETE | `delete_user()` | Deletes a user. Prevents self-delete. | Admin |
| `/api/v1/admin/users/{user_id}/reset-password` | POST | `reset_password()` | Sets new password hash for a user. | Admin |
| `/api/v1/admin/users/pending-count` | GET | `pending_count()` | Counts users who have not visited settings. | Admin |
| `/api/v1/admin/users/mark-visited` | POST | `mark_settings_visited()` | Marks current user's settings as visited. | Authenticated |

## 2.5 Conversation and Chat API

Router: `src/server/conversations/router.py`  
Prefix: `/api/conversations`

| Route | Method | Function | Purpose | Auth |
|---|---:|---|---|---|
| `/api/conversations` | GET | `list_conversations()` | Lists conversations for the current user. | Required |
| `/api/conversations` | POST | `create_conversation()` | Creates a conversation for the current user. | Required |
| `/api/conversations/{conversation_id}` | GET | `get_conversation()` | Returns a conversation plus messages. | Required |
| `/api/conversations/{conversation_id}/source-tree` | GET | `get_source_tree()` | Returns latest source tree snapshot for a conversation. | Required |
| `/api/conversations/{conversation_id}/messages` | POST | `post_message()` | Streams a chat turn as NDJSON. | Required |

### Chat Request Schema

Defined in `src/server/conversations/schemas.py`:

- `PostMessageRequest.content`
- `PostMessageRequest.mode`
- `PostMessageRequest.selected_context`
- `PostMessageRequest.history_turns`
- `PostMessageRequest.retrieval_settings`

Supported `QueryMode` values:

- `local`
- `global`
- `hybrid`
- `naive`
- `mix`

`RetrievalSettings` includes:

- `lightrag_port`
- `top_k`
- `chunk_top_k`
- `chunk_rerank_top_k`
- `max_entity_tokens`
- `max_relation_tokens`
- `max_total_tokens`
- `document_ids`
- `full_doc_ids`
- `chunk_ids`

### Chat Stream Event Flow

Implemented in `src/server/context/stream_service.py`, function `run_chat_turn()`:

```text
User POST /api/conversations/{id}/messages
   │
   ├── create user message
   ├── create placeholder assistant message
   ├── yield metadata event
   ├── yield progress: preparing
   ├── retrieve context unless selected_context provided
   ├── yield context event
   ├── save source tree snapshot
   ├── call LightRAG /query
   ├── yield token events
   ├── mark assistant message completed
   └── yield done event
```

On exception:

```text
mark assistant message failed
yield error event
yield done event
```

## 2.6 LightRAG Domain and Graph Proxy API

Router: `src/server/lightrag/router.py`  
Prefix: `/api/lightrag`

| Route | Method | Function | Purpose | Auth / Permission |
|---|---:|---|---|---|
| `/api/lightrag/domains` | GET | `list_domains()` | Lists discovered healthy LightRAG domains or fallback domain. | Auth required |
| `/api/lightrag/entity-types` | GET | `entity_types()` | Returns default LightRAG entity types from `lightrag.prompt.PROMPTS`. | Auth required |
| `/api/lightrag/domains/{port}/graphs` | GET | `graphs()` | Proxies graph fetch to selected LightRAG domain. | Auth required |
| `/api/lightrag/domains/{port}/graph/label/popular` | GET | `popular_labels()` | Proxies popular graph labels. | Auth required |
| `/api/lightrag/domains/{port}/graph/label/search` | GET | `search_labels()` | Proxies label search. | Auth required |
| `/api/lightrag/domains/{port}/graph/entity/exists` | GET | `entity_exists()` | Proxies entity existence check. | Auth required |
| `/api/lightrag/domains/{port}/graph/entity/edit` | POST | `edit_entity()` | Proxies graph entity update. | Admin or `can_write` |
| `/api/lightrag/domains/{port}/graph/relation/edit` | POST | `edit_relation()` | Proxies graph relation update. | Admin or `can_write` |

Supporting files:

| File | Responsibility |
|---|---|
| `src/server/lightrag/domain_service.py` | Reads `data/domains.json`, checks `/health`, builds available domain list. |
| `src/server/lightrag/graph_proxy.py` | Validates requested port against discovered domains and forwards HTTP requests to LightRAG. |

## 2.7 Native LightRAG API Surface

The repo includes a vendored/modified LightRAG server under `src/lightrag/api/`.

Observed router files:

| File | Likely Surface |
|---|---|
| `src/lightrag/api/routers/document_routes.py` | Document upload/index/scan/document status operations. |
| `src/lightrag/api/routers/graph_routes.py` | Graph visualization/edit/search operations. |
| `src/lightrag/api/routers/query_routes.py` | Query/context retrieval operations such as `/query` and `/query/context`. |
| `src/lightrag/api/routers/ollama_api.py` | Ollama-compatible API surface. |

The custom backend calls the native LightRAG API in two main ways:

| Backend File / Function | Native LightRAG Endpoint |
|---|---|
| `src/server/context/retrieval_service.py` / `retrieve_context()` | `POST {base_url}/query/context` |
| `src/server/context/stream_service.py` / `query_lightrag()` | `POST {base_url}/query` |
| `src/server/lightrag/graph_proxy.py` / proxy helpers | Graph endpoints under selected LightRAG domain. |

## 2.8 API Gaps / Unknowns

| Area | Status |
|---|---|
| Full native LightRAG document endpoint enumeration | Not fully enumerated in this review. Inspect `src/lightrag/api/routers/document_routes.py` locally. |
| API-level document upload in custom `src/server` backend | Not observed. Document ingestion appears to rely on native LightRAG container/API/UI or domain input dirs. |
| OpenAPI schema snapshot | Not generated in this review because the repo could not be cloned locally. |
| Request/response models for every native LightRAG route | Unknown from current review. |
