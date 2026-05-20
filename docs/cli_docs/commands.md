# Operator capability map (`context-engine` TUI ↔ REST)

The launcher **`context-engine`** / **`context-tui`** exposes **only** the interactive terminal UI (`cli.launcher:main`). The tables below tie **capabilities** operators reach through menus to canonical **HTTP verbs and paths**.

For request/response field detail, reuse `docs/cli_docs/api-contract.md`.

## Launcher options

Parsed in **`cli/config.py`**:

```bash
context-engine --api-base-url http://127.0.0.1:8010 --config-dir ~/.context-engine/cli
context-engine --no-keyring
```

| Option / env | Role |
| --- | --- |
| **`--api-base-url`**, or **`CONTEXT_ENGINE_API_BASE_URL`** | Backend root URL (`http`/`https`; trailing slash tolerated) |
| **`--config-dir`** | Directory for persisted session files when not using defaults |
| **`--keyring` / `--no-keyring`** | Toggle OS credential keyring backing vs file-only fallback |

Scripts should call **REST endpoints** directly—not launch the TUI with fake “subcommands”.

## Session and identity

| UI intent | Approximate REST |
| --- | --- |
| Sign-in | **`POST /auth/login`** `{ email, password }` |
| Sign-out locally | Credential clear (**local only**) |
| Current user/session summary | **`GET /auth/me`** |

`/auth/login` returns `{access_token, token_type}`. The client stores **`api_base_url` + bearer token**. Password material is requested only transiently during login.

## Documents and retrieval

| UI intent | REST |
| --- | --- |
| List corpora ready documents | **`GET /documents`** |
| Document detail | **`GET /documents/{document_id}`** |
| Document structure/outline | **`GET /documents/{document_id}/structure`** |
| Parsed page body | **`GET /documents/{document_id}/pages/{page_number}`** |
| Retrieval-only answers | **`POST /query/retrieve`** |
| Composed citation answer | **`POST /query/answer`** or **`POST /query`** shortcut |

Representative **`POST /query/retrieve`** body:

```json
{
  "query": "where are installation steps",
  "mode": "auto",
  "top_k": 5,
  "include_debug": false,
  "allow_general_fallback": false,
  "document_ids": ["doc_123"],
  "lightrag_domain_id": "fatigue"
}
```

`document_ids` and `lightrag_domain_id` are omitted unless filters/domain selection apply. **`include_debug`** is honored only for admins on the backend. Supported modes: **`auto`**, **`semantic`**, **`navigation`**, **`hybrid`** (routing policy respects **`LIGHTRAG_ENABLED`** as documented elsewhere).

Known **backend gaps** (examples only—currently no matching routes):

- Multi-page **`documents content`** slicing as a standalone command  
- Dedicated document **text search** endpoint separate from retrieval

## LightRAG graph reads

| UI intent | REST |
| --- | --- |
| Graph summary (`label`, depth knobs) | **`GET /graphs`** with query params per backend schema |
| Label catalog/list | **`GET /graph/label/list`** |
| Popular labels | **`GET /graph/label/popular`** |
| Label search | **`GET /graph/label/search?q=…`** |

The UI never connects to LightRAG directly; backend proxy handles **`LIGHTRAG_ENABLED`** and outbound HTTP.

In the TUI root menu this area is labeled **`Graphs`**.

## LightRAG domain lifecycle

| UI intent | REST |
| --- | --- |
| List user-selectable retrieval domains | **`GET /lightrag/domains`** |
| List configured domains | **`GET /admin/lightrag/domains`** |
| Create domain | **`POST /admin/lightrag/domains`** |
| Show domain detail | **`GET /admin/lightrag/domains/{domain_id}`** |
| Start domain | **`POST /admin/lightrag/domains/{domain_id}/up`** |
| Stop domain | **`POST /admin/lightrag/domains/{domain_id}/down`** |
| Recreate domain | **`POST /admin/lightrag/domains/{domain_id}/recreate`** |
| Regenerate domain files | **`POST /admin/lightrag/domains/{domain_id}/regenerate`** |
| Archive remove | **`DELETE /admin/lightrag/domains/{domain_id}`** |
| Permanent delete | **`DELETE /admin/lightrag/domains/{domain_id}?permanent=true`** |

Create body:

```json
{
  "domain_id": "fatigue",
  "display_name": "Fatigue Manuals",
  "host_port": 9622,
  "make_default": true
}
```

Domain deploy screens are admin-only through backend authorization. **`LIGHTRAG_DEPLOY_ENABLED=true`** must be set for deployment operations. Permanent delete additionally requires backend support via **`LIGHTRAG_ALLOW_PERMANENT_DELETE=true`**; otherwise the TUI shows the backend error.

## Admin document operations

| UI intent | REST |
| --- | --- |
| Upload | **`POST /admin/documents/upload`** (`multipart/form-data`; fields **`file`**, optional **`semantic_engine=lightrag`**, optional **`lightrag_domain_id`**) |
| List all docs (admin lens) | **`GET /admin/documents`** |
| Index · reindex · delete | **`POST /admin/documents/{id}/index`** · **`/reindex`** · **`DELETE /admin/documents/{id}`** |
| Planned corpus lifecycle knobs | Backend routes **missing** (`publish`, `rollback`, …) |

LightRAG uploads enqueue a **`lightrag_ingest_document`** job and return queued **`lightrag.*`** metadata. Optional navigation processing is tracked separately under **`metadata.navigation`**.

In the TUI, these operations are nested under **`Documents -> Admin Actions`** (not a separate root menu item).

## Observability (admin)

| UI intent | REST |
| --- | --- |
| Audit trail | **`GET /admin/audit-logs`** |
| Query / retrieval history | **`GET /admin/query-logs`** |

## Jobs (admin)

| UI intent | REST |
| --- | --- |
| List jobs | **`GET /jobs`** |
| Job detail | **`GET /jobs/{job_id}`** |
| Retry failed job | **`POST /jobs/{job_id}/retry`** |

Jobs track local worker-owned indexing pipelines.

## Planned-only backend surface

Future FastAPI endpoints would back chat, richer user administration, conversational agents/runs approvals, corpus lifecycle tooling, etc. Until those handlers exist:

- Screens under **Backend Gaps** or equivalent should surface deterministic **`not_supported_by_backend`**-style explanations—matching what earlier Typer stubs returned.

See **`docs/cli_docs/api-contract.md`** § *Planned surface*.

## Automation JSON snippets

Representative payloads mirror backend responses—for example **`GET /documents`**:

```json
{
  "documents": [
    {
      "id": "doc_123",
      "filename": "manual.pdf",
      "status": "ready"
    }
  ]
}
```

For retrieval with **`include_debug=true`** (admin-only echoes):

```json
{
  "query": "installation steps",
  "mode": "navigation",
  "evidence": [
    {
      "evidence_id": "nav-1",
      "document_id": "doc_123",
      "source_engine": "navigation",
      "text": "Installation steps...",
      "score": 0.8,
      "page_start": 1,
      "page_end": 1,
      "section_title": "Installation",
      "metadata": {}
    }
  ],
  "debug": {
    "requested_mode": "auto",
    "selected_engine": "navigation"
  }
}
```

Normal users omit **`debug`** even when callers request **`include_debug`**.
