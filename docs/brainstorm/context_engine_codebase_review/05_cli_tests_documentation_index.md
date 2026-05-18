# 5. CLI, Tests, and Documentation Index

## 5.1 CLI Overview

CLI package:

- `cli/main.py`
- `cli/api_client.py`
- `cli/credentials.py`

Console script:

```text
ragcli = "cli.main:app"
```

The CLI is a thin API client. It does not bypass backend permissions. It stores the API base URL and bearer token after login.

Credential behavior:

1. Try OS keyring.
2. If unavailable, fallback to a local JSON file:

```text
~/.context-engine/ragcli/credentials.json
```

Fallback file permission is attempted as `0600`.

## 5.2 Implemented CLI Commands

| Command | Backend Route | Auth | Purpose |
|---|---|---|---|
| `ragcli login` | `POST /auth/login` | Public | Login and save token. |
| `ragcli logout` | local only | n/a | Clear stored credentials. |
| `ragcli auth me` | `GET /auth/me` | User | Show current user. |
| `ragcli documents list` | `GET /documents` | User | List ready documents. |
| `ragcli documents show` | `GET /documents/{id}` | User | Show document details. |
| `ragcli documents structure` | `GET /documents/{id}/structure` | User | Show navigation tree. |
| `ragcli documents page` | `GET /documents/{id}/pages/{page}` | User | Show parsed page. |
| `ragcli documents retrieve` | `POST /query/retrieve` | User | Run retrieval only. |
| `ragcli documents answer` | `POST /query/answer` | User | Run retrieval + answer. |
| `ragcli query` | `POST /query` | User | Convenience query command. |
| `ragcli admin documents upload` | `POST /admin/documents/upload` | Admin | Upload document. |
| `ragcli admin documents index` | `POST /admin/documents/{id}/index` | Admin | Start/queue index. |
| `ragcli admin documents reindex` | `POST /admin/documents/{id}/reindex` | Admin | Start/queue reindex. |
| `ragcli admin documents delete` | `DELETE /admin/documents/{id}` | Admin | Mark document deleted. |
| `ragcli admin documents list` | `GET /admin/documents` | Admin | List all documents. |
| `ragcli jobs list` | `GET /jobs` | Admin | List jobs. |
| `ragcli jobs status` | `GET /jobs/{id}` | Admin | Show job status. |
| `ragcli jobs retry` | `POST /jobs/{id}/retry` | Admin | Retry job. |

## 5.3 Planned / Unsupported CLI Commands

The CLI includes placeholder command groups that return `not_supported_by_backend` until backend routes exist.

| Command Area | Examples | Status |
|---|---|---|
| Corpus management | `ragcli admin corpus publish`, `rollback`, `cleanup` | Placeholder only. |
| Users | `ragcli users create`, `users list` | Placeholder only. |
| Agents | `ragcli agents list` | Placeholder only. |
| Retrievers | `ragcli retrievers list` | Placeholder only. |
| Conversations | `create`, `list`, `show` | Placeholder only. |
| Chat | `ragcli chat` | Placeholder only. |
| Messages | `send`, `list` | Placeholder only. |
| Runs/approvals | `status`, `cancel`, `approvals list/approve/reject` | Placeholder only. |

Design note: placeholders are useful for future API planning, but they may confuse junior developers/users unless clearly documented as not implemented.

## 5.4 CLI Design Recommendations

Keep:

- API-first design.
- `--output json` support for scripting/testing.
- Small `ApiClient` with standard library HTTP calls.
- Keyring-first credential storage.

Improve soon:

- Add `ragcli admin system status` once backend has system status.
- Add clearer help text showing which commands are implemented vs planned.
- Consider moving unsupported future command groups behind an experimental flag or docs page.
- Add examples to README:

```bash
ragcli login --email admin@example.com
ragcli admin documents upload --file ./manual.pdf
ragcli jobs list
ragcli documents retrieve --query "installation steps"
```

## 5.5 Test Suite Inventory

The `tests/` folder includes:

| Test File | What It Appears to Cover |
|---|---|
| `test_api.py` | Main API flow: health, auth guardrails, upload, document visibility, retrieve, answer, LightRAG enabled behavior, graph proxy, job queue behavior, worker failure behavior. |
| `test_cli.py` | CLI behavior. Exact contents were not fully expanded in the static web view. |
| `test_cli_ascii_samples.py` | CLI ASCII sample rendering. |
| `test_cli_query_payload.py` | CLI query payload construction. |
| `test_cli_screen_renderers.py` | TUI/screen renderer behavior. |
| `test_cli_tui.py` | Interactive/TUI behavior. |
| `test_answer_composer.py` | Answer composition logic. |
| `test_evidence_mapper.py` | Evidence/page/source mapping. |
| `test_lightrag_remote_adapter.py` | Remote LightRAG adapter behavior. |
| `test_retrieval_routing_policy.py` | Local vs remote/mode routing policy. |
| `fixtures/` | Test fixture data. |

Observed from `test_api.py`:

- Tests set `DATABASE_URL=sqlite:///./.data/test_context_engine.db`.
- Tests set `INDEX_JOBS_INLINE=true`.
- Tests set `LIGHTRAG_ENABLED=false` by default.
- Tests seed admin and normal user accounts directly through repositories.
- Tests verify normal users cannot access admin ping/upload.
- Tests verify non-ready documents are hidden from normal-user document read APIs.
- Tests verify remote LightRAG retrieval/upload paths with monkeypatched adapter methods.
- Tests verify graph proxy routes use upstream route names like `/graphs` and `/graph/label/list`.
- Tests verify queued jobs can be enqueued without inline execution.
- Tests verify worker marks an indexing job failed when the document is missing.

## 5.6 Minimum Useful Tests to Add Next

| Priority | Test | Why |
|---:|---|---|
| 1 | Production config guard test | Ensure default `SECRET_KEY` fails or warns in production. |
| 2 | Upload validation tests | Protect file size/type assumptions. |
| 3 | Concurrent reindex guard test | Prevent duplicate running jobs per document. |
| 4 | Admin logs pagination/limits test | Prevent unbounded log responses. |
| 5 | CLI implemented-vs-planned command test | Avoid confusing unsupported placeholders. |
| 6 | LightRAG unavailable upload test | Ensure local document is marked failed and stable error returned. |
| 7 | Retrieval ignores failed/deleted docs test | Protect query correctness. |
| 8 | Worker/Redis readiness test | Useful for deployment diagnostics. |

## 5.7 Documentation-vs-Code Review Notes

Because docs and brainstorm folders may include future plans, future coding agents should use this rule:

```text
Code is source of truth.
Docs are helpful only after checking the matching route/service/test exists.
Brainstorm docs are not implementation evidence.
```

Suggested doc classifications:

| Doc Type | How to Treat It |
|---|---|
| README | High-trust for setup flow, but still verify against code. |
| API contract docs | Useful if route files/tests confirm them. |
| CLI docs | Useful if `cli/main.py` confirms commands. |
| Brainstorm docs | Architecture ideas only. Do not assume implemented. |
| Prompt/reference docs | Useful for project intent, not runtime behavior. |

## 5.8 Recommended Documentation Cleanup

Add or update these docs in the repo:

1. `docs/codebase-map.md`
2. `docs/api-surface.md`
3. `docs/configuration.md`
4. `docs/admin-workflows.md`
5. `docs/ragcli-implemented-commands.md`
6. `docs/lightrag-integration.md`
7. `docs/deployment-local-network.md`
8. `docs/testing-strategy.md`

Keep them short and link to files/functions instead of duplicating too much code.
