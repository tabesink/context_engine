# Terminal client ←→ backend contract

Maps **capabilities operators reach via the `context-engine`/`context-tui` Rich terminal UI** to the backend that exists today. Items marked **`supported`** call concrete FastAPI routes through `cli/api_client.py`. Backend gaps are documented separately and are not exposed as successful TUI actions.

Older Typer-era subcommands were named **`ragcli …`**; shipping entrypoints are **`context-engine`** and **`context-tui`** only (**`cli.launcher:main`**).

## Auth

| TUI capability | Backend | Role | Status |
| --- | --- | --- | --- |
| Login (credentials prompt) | **`POST /auth/login`** `{email, password}` | public | supported |
| Log out / clear locals | Discard stored token (**local**) | local | supported |
| Session overview | **`GET /auth/me`** | authenticated | supported |

`/auth/login` returns `{access_token, token_type}`. The launcher stores **`api_base_url` + bearer token** only—never passwords—and warns when a new `--api-base-url` disagrees with the stored login host.

## Documents and retrieval

| TUI capability | Backend | Role | Status |
| --- | --- | --- | --- |
| Browse document library | `GET /documents` | authenticated | supported |
| Document detail | `GET /documents/{document_id}` | authenticated | supported |
| Structure/outline | `GET /documents/{document_id}/structure` | authenticated | supported |
| Parsed page preview | `GET /documents/{document_id}/pages/{page_number}` | authenticated | supported |
| Retrieval preview | `POST /retrieve` | authenticated | supported |
| Scoped retrieval (doc filters) | Same route with `document_ids` in JSON body | authenticated | supported |
| Multi-page `content` helper | no range endpoint | authenticated | documented gap |
| Dedicated search endpoint | no separate search route | authenticated | documented gap |

Sample retrieve body:

```json
{
  "query": "where are installation steps",
  "mode": "auto",
  "top_k": 5,
  "include_debug": false,
  "document_ids": ["doc_123"]
}
```

`include_debug` is accepted on retrieve requests, but **only admins** receive debug payloads from the backend.

## LightRAG graphs

| TUI capability | Backend | Role | Status |
| --- | --- | --- | --- |
| Graph summary with label and limits | `GET /graphs?label=…&max_depth=…&max_nodes=…` | authenticated | supported |
| Label catalog | `GET /graph/label/list` | authenticated | supported |
| Popular labels | `GET /graph/label/popular?limit=…` | authenticated | supported |
| Label search | `GET /graph/label/search?q=…&limit=…` | authenticated | supported |

Requires backend **`LIGHTRAG_ENABLED=true`** (mandatory at startup) with a reachable remote LightRAG service. LightRAG outages surface as HTTP `502`/`503` integration errors; there is no local semantic fallback.

This capability is surfaced as **`Graphs`** in the root TUI menu.

## LightRAG domains

| TUI capability | Backend | Role | Status |
| --- | --- | --- | --- |
| Retrieval domain picker | `GET /lightrag/domains` | authenticated | supported |
| Domain overview | `GET /admin/lightrag/domains` | admin | supported |
| Create domain | `POST /admin/lightrag/domains` | admin | supported |
| Start domain | `POST /admin/lightrag/domains/{domain_id}/up` | admin | supported |
| Stop domain | `POST /admin/lightrag/domains/{domain_id}/down` | admin | supported |
| Recreate domain | `POST /admin/lightrag/domains/{domain_id}/recreate` | admin | supported |
| Archive remove | `DELETE /admin/lightrag/domains/{domain_id}` | admin | supported |
| Permanent delete | `DELETE /admin/lightrag/domains/{domain_id}?permanent=true` | admin | supported when enabled |

Create accepts:

```json
{
  "domain_id": "fatigue",
  "display_name": "Fatigue Manuals",
  "host_port": 9622,
  "make_default": true
}
```

Admin domain routes require **`LIGHTRAG_DEPLOY_ENABLED=true`**. Runtime graph/retrieval behavior remains controlled separately by **`LIGHTRAG_ENABLED`**, **`LIGHTRAG_BASE_URL`**, and optional **`LIGHTRAG_API_KEY`**. The runtime **`LIGHTRAG_DOMAIN_MANIFEST`** and deploy **`LIGHTRAG_DOMAINS_MANIFEST`** default to the same file path but are separate settings.

## Admin documents

| TUI capability | Backend | Role | Status |
| --- | --- | --- | --- |
| Upload | `POST /admin/documents/upload` (`multipart/form-data`, field `file`) | admin | supported |
| Reingest | `POST /admin/documents/{document_id}/reingest` | admin | supported |
| Refresh status | `POST /admin/documents/{document_id}/refresh-status` | admin | supported |
| Delete | `DELETE /admin/documents/{document_id}` | admin | supported |
| Admin listing | `GET /admin/documents` | admin | supported |
| Corpus publish/rollback/cleanup | no matching endpoints | admin | documented gap |

These admin routes are surfaced from **`Documents -> Admin Actions`** in the TUI (not a standalone root menu).

## Admin observability

| TUI capability | Backend | Role | Status |
| --- | --- | --- | --- |
| Audit feed | `GET /admin/audit-logs` | admin | supported |
| Query log feed | `GET /admin/query-logs` | admin | supported |

## Jobs

| TUI capability | Backend | Role | Status |
| --- | --- | --- | --- |
| List jobs | `GET /jobs` | admin | supported |
| Job detail | `GET /jobs/{job_id}` | admin | supported |
| Retry | `POST /jobs/{job_id}/retry` | admin | supported |

## Planned surface

These ideas once mapped to Typer stubs; backends still lack matching contracts. Keep them out of the root TUI until behavior plus tests land, and track them in `docs/cli_docs/backend_gaps.md`:

- User administration (`POST /users`, `GET /users`, …)
- Retriever registry / agent registry (`GET /retrievers`, `GET /agents`)
- Conversations & chat (`/conversations`, `/chat`, `/messages`, …)
- Agent runs & approvals (`/runs/*`, `/runs/approvals/*`)
- Corpus lifecycle publish/rollback/cleanup
