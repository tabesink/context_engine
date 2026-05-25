# 7. Tests, Risks, and Coding Agent Safety Notes

## 7.1 Observed Test Files

| Test File | Area Suggested by Name / Observed Imports | Notes |
|---|---|---|
| `tests/test_backend_auth_and_users.py` | Auth, admin user lifecycle, conversation scoping, rate limits. | Imports `backend.*` in observed content. |
| `tests/test_backend_chat_service.py` | Chat stream event order, context retrieval, failure behavior, selected context behavior, source projection. | Imports `backend.services.*`, which may not match visible `src/server` namespace. |
| `tests/test_backend_health.py` | Health endpoint and settings normalization. | References backend app/settings. |
| `tests/test_backend_lightrag_graph_proxy.py` | Graph proxy forwarding, invalid domain ports, entity types, graph write permissions. | Good behavioral target for current `src/server/lightrag`. |
| `tests/test_backend_repositories.py` | Repository behavior for conversations, retrieval frames, source trees, synthesis runs. | Appears to reference repository classes not visible under current `src/server/storage/repositories`. |
| `tests/test_lightrag_gateway.py` | LightRAG gateway behavior for `/query/context`, navigation context, errors. | Appears to reference a `backend.gateways` layer not visible in current inspected tree. |
| `tests/test_lightrag_citations.py` | LightRAG citation behavior. | Inspect locally before modifying citation/structural chunking code. |
| `tests/test_mcp_config_and_client.py` | MCP config/client behavior. | Related to `lightrag-mcp-server` script entry point. |
| `tests/test_mcp_integration.py` | MCP integration. | Needs local inspection. |
| `tests/test_mcp_smoke.py` | MCP smoke coverage. | Needs local inspection. |
| `tests/test_server_minimal.py` | Minimal server behavior. | Needs local inspection. |
| `tests/test_source_tree_indexer.py` | Source tree indexing behavior. | Likely related to context/source tree UI. |
| `tests/test_structural_chunking.py` | Structural chunking behavior. | Important before editing `src/lightrag/structural_chunking.py`. |
| `tests/test_turn_planner.py` | Turn planning behavior. | Needs local inspection. |

## 7.2 Major Test Namespace Warning

Visible runtime code is under:

```text
src/server/
```

But several observed tests and `pyproject.toml` references point to:

```text
backend
src/backend
```

Examples:

- `pyproject.toml` script entry point: `lightrag-backend = "backend.main:main"`
- `pyproject.toml` package mapping: `backend = src/backend`
- Observed tests import modules like `backend.app`, `backend.config`, `backend.repositories`, `backend.services`.
- The visible `src/` listing showed `agent`, `lightrag`, `lightrag_webui`, and `server`, not `backend`.

This is a high-priority alignment issue. Before using the tests as a safety net, confirm whether:

1. `src/backend` exists locally but was not visible in web listing;
2. tests are stale from an earlier backend implementation;
3. package mapping is stale;
4. `server` is intended to replace `backend`.

Do not refactor backend namespaces until this is understood.

## 7.3 What Behavior Tests Appear to Protect

| Behavior | Test Evidence |
|---|---|
| Admin bootstrap/login/logout/me | `tests/test_backend_auth_and_users.py` |
| User lifecycle and permissions | `tests/test_backend_auth_and_users.py` |
| Per-user conversation scoping | `tests/test_backend_auth_and_users.py` |
| Chat rate limiting | `tests/test_backend_auth_and_users.py` |
| Chat stream event order | `tests/test_backend_chat_service.py` |
| Context event before tokens | `tests/test_backend_chat_service.py` |
| Retrieval failure emits error and done | `tests/test_backend_chat_service.py` |
| Selected context skips retrieval | `tests/test_backend_chat_service.py` |
| Source projection ordering | `tests/test_backend_chat_service.py` |
| Health endpoint | `tests/test_backend_health.py` |
| Graph proxy forwarding and permission | `tests/test_backend_lightrag_graph_proxy.py` |
| Repository persistence semantics | `tests/test_backend_repositories.py`, although namespace may be stale. |
| LightRAG gateway request shaping/errors | `tests/test_lightrag_gateway.py`, although namespace may be stale. |
| Structural chunking | `tests/test_structural_chunking.py` |

## 7.4 High-Severity Risks

| Risk | Evidence | Why It Matters | Suggested Direction |
|---|---|---|---|
| Backend namespace mismatch | Runtime code visible under `src/server`; tests and pyproject reference `backend`. | Tests may not run against actual code. Coding agents may modify wrong namespace. | First establish canonical backend package. Update scripts/tests/docs only after confirming intent. |
| Backend DB path mismatch | `.env.example` uses `data/backend/backend.sqlite3`; `src/server/config/settings.py` defaults to `data/server/server.sqlite3`. | Data may appear missing depending on startup path. | Decide canonical path and update docs/env/tests consistently. |
| Default admin/JWT secrets in example | `.env.example` includes `admin/admin123` and `change-me-local-dev-secret`. | Dangerous if copied into non-local deployment. | Add explicit local-only warnings and require secret generation for real deployments. |
| Domain deletion behavior | `_remove_domain()` archives/removes active domain dir. | Operator can accidentally remove source/index/artifact data. | Add dry-run/confirmation/backups before using in production-like data. |
| Shared storage reset risk | PostgreSQL/Redis/Neo4j are shared across domains. | Resetting shared services can affect multiple knowledge bases. | Document reset procedures separately for dev vs real data. |

## 7.5 Medium-Severity Risks

| Risk | Evidence | Why It Matters | Suggested Direction |
|---|---|---|---|
| Two UI layers | `client/` and `src/lightrag_webui/` both exist. | Developers may improve one while users use the other. | Explicitly document active UI direction. |
| Domain discovery health timing | `discover_domains()` checks health and falls back if none healthy. | Backend startup before domains may hide available domains. | Add refresh endpoint or client-triggered reload if needed. |
| Localhost LightRAG base URL construction | `_lightrag_base_url()` uses `http://127.0.0.1:{port}` when port provided. | Backend inside Docker would not reach host localhost domain containers. | Keep local-only assumption or make network base configurable. |
| Rate-limit event growth | `rate_limit_events` inserts events; no pruning observed. | Long-running server can grow DB. | Add retention cleanup or bucket aggregation. |
| Scripts not reconciled with CLI | `scripts/*.sh` exist; CLI also handles deployment. | Duplication can cause confusing operator workflows. | Decide whether CLI or scripts are canonical. |
| Root README missing or inaccessible | `pyproject.toml` references `README.md`; raw README returned 404 during review. | Package metadata/doc onboarding may break. | Add or restore root README. |

## 7.6 Low-Severity Risks

| Risk | Why It Matters | Suggested Direction |
|---|---|---|
| Screenshot/file typos | Filenames like `graphveiw_card.png`, `lightrag_retreival_settings.png`. | Minor polish/readability issue. | Avoid changing unless docs/assets are being cleaned. |
| Large one-line files in raw view | Some files appeared as a single line in raw fetch. | Makes review/diffs harder if formatting is actually compressed. | Confirm local formatting before editing. |
| Aspirational docs vs implementation | Docs/prompts/screenshots may reflect future design. | Coding agents may follow docs instead of code. | Build a docs-vs-code matrix before refactor. |

## 7.7 Files That Are Safer to Edit First

These are good candidates for documentation or small cleanup after tests are understood:

| Path | Why Safer |
|---|---|
| `docs/` | Documentation-only changes, lower runtime risk. |
| `AGENTS.md` | Coding-agent guidance. Useful once canonical architecture is confirmed. |
| `.env.example` | Can improve warnings/comments, but coordinate DB path decision first. |
| `client/src/api/*` | API client clarity improvements, if backend routes are stable. |
| `client/src/stores/*` | UI-state cleanup, if covered manually and not touching backend data. |

## 7.8 Files That Are Dangerous to Edit Casually

| Path | Why Dangerous |
|---|---|
| `cli/main.py` | Controls domain lifecycle, secrets, compose generation, deletion/archive behavior. |
| `docker-compose.domains.yml` | Controls shared services, ports, volumes, and domain runtime. |
| `Dockerfile.lightrag-local` | Controls runtime image and local LightRAG override. |
| `src/lightrag/*` | Vendored/modified LightRAG code; changes affect indexing, retrieval, graph. |
| `src/lightrag/structural_chunking.py` | Affects chunk metadata, artifacts, source tree, citations. |
| `src/server/storage/db.py` | Schema changes can break existing SQLite data. |
| `src/server/auth/security.py` | Auth/cookies/JWT/password security. |
| `data/` | Contains runtime data, secrets, indexes, graph/vector storage, domain corpora. |

## 7.9 Commands a Developer Should Run Before Changes

Confirm locally before using these exact commands; names may need adjustment depending on environment.

```bash
# inspect package config
uv run python -c "import sys; print(sys.version)"

# run tests
uv run pytest

# run a focused backend/auth test group
uv run pytest tests/test_backend_auth_and_users.py

# run structural chunking tests before touching src/lightrag/structural_chunking.py
uv run pytest tests/test_structural_chunking.py

# inspect CLI help
uv run lightrag-cli --help
uv run lightrag-cli domain --help

# validate generated compose config after CLI/domain changes
docker compose -f docker-compose.domains.yml config
```

## 7.10 Coding Agent Safety Checklist

Before modifying code, a future coding agent should answer:

- Is `server` or `backend` the canonical backend package?
- Which UI is canonical: `client/` or `src/lightrag_webui/`?
- Is the repo currently intended for local trusted network only?
- Should the backend run on host or inside Docker?
- Which SQLite DB path is canonical?
- Is `docker-compose.domains.yml` hand-edited or always generated by CLI?
- Are scripts under `scripts/` still used, or should the CLI be the canonical operator interface?
- What data under `data/` must never be deleted?
- Are LightRAG customizations intentionally forked from upstream?
- Which tests are current and which are stale?

## 7.11 Recommended Next Refactor Planning Order

Do not refactor immediately. Recommended next planning order:

1. **Namespace reconciliation**: confirm `src/server` vs `backend` and make tests/package metadata align.
2. **Docs baseline**: add a root README explaining CLI, backend, client, domain runtime, and data safety.
3. **Operator safety**: document domain deletion/archive behavior and shared storage reset procedures.
4. **Config centralization**: resolve DB path and localhost/container assumptions.
5. **Test restoration**: ensure tests run against current code before behavior changes.
6. **API surface snapshot**: generate OpenAPI from running backend and document native LightRAG routes.
7. **UI direction**: decide whether custom Next.js client or LightRAG WebUI is the primary interface.
8. **LightRAG integration boundary**: clearly separate vendored upstream code from local modifications.
