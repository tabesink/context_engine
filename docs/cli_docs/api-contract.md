# CLI API Contract

This contract maps the desired `ragcli` surface to the backend that exists today. Commands marked `supported` can be implemented directly. Commands marked `backend gap` need backend behavior before they should become real commands.

## Auth

| Command | Backend | Role | Status |
| --- | --- | --- | --- |
| `ragcli login --email EMAIL` | `POST /auth/login` with `{email, password}` | public | supported |
| `ragcli logout` | local credential clear | local | supported |
| `ragcli auth me` | `GET /auth/me` | authenticated | supported |

`/auth/login` returns `{access_token, token_type}`. The CLI stores only the API base URL and access token.

## Documents And Retrieval

| Command | Backend | Role | Status |
| --- | --- | --- | --- |
| `ragcli documents list` | `GET /documents` | authenticated | supported |
| `ragcli documents show --document-id ID` | `GET /documents/{document_id}` | authenticated | supported |
| `ragcli documents structure --document-id ID` | `GET /documents/{document_id}/structure` | authenticated | supported |
| `ragcli documents page --document-id ID --page-number N` | `GET /documents/{document_id}/pages/{page_number}` | authenticated | supported |
| `ragcli documents retrieve --query TEXT` | `POST /query/retrieve` | authenticated | supported |
| `ragcli documents answer --query TEXT` | `POST /query/answer` | authenticated | supported |
| `ragcli query --query TEXT` | `POST /query` | authenticated | supported |
| `ragcli documents content --pages 1-3` | no range endpoint | authenticated | backend gap |
| `ragcli documents search --query TEXT` | no separate search endpoint | authenticated | backend gap |

Retrieval request body:

```json
{
  "query": "where are installation steps",
  "mode": "auto",
  "top_k": 5,
  "allow_general_fallback": false
}
```

## Admin Documents

| Command | Backend | Role | Status |
| --- | --- | --- | --- |
| `ragcli admin documents upload --file PATH` | `POST /admin/documents/upload` multipart field `file` | admin | supported |
| `ragcli admin documents index --document-id ID` | `POST /admin/documents/{document_id}/index` | admin | supported |
| `ragcli admin documents reindex --document-id ID` | `POST /admin/documents/{document_id}/reindex` | admin | supported |
| `ragcli admin documents delete --document-id ID` | `DELETE /admin/documents/{document_id}` | admin | supported |
| `ragcli admin documents list` | `GET /admin/documents` | admin | supported |
| `ragcli admin corpus publish` | no corpus version endpoint | admin | backend gap |
| `ragcli admin corpus rollback` | no corpus version endpoint | admin | backend gap |
| `ragcli admin corpus cleanup` | no corpus cleanup endpoint | admin | backend gap |

## Jobs

| Command | Backend | Role | Status |
| --- | --- | --- | --- |
| `ragcli jobs list` | `GET /jobs` | admin | supported |
| `ragcli jobs status --job-id ID` | `GET /jobs/{job_id}` | admin | supported |
| `ragcli jobs retry --job-id ID` | `POST /jobs/{job_id}/retry` | admin | supported |

## Planned Surface

These commands are part of the full prompt surface, but the current backend has no matching route contract:

- `ragcli users create`
- `ragcli users list`
- `ragcli retrievers list`
- `ragcli agents list`
- `ragcli conversations create/list/show`
- `ragcli chat`
- `ragcli messages send/list`
- `ragcli runs status/cancel`
- `ragcli runs approvals list/approve/reject`

Until backend behavior exists, these commands should return a structured `not_supported_by_backend` error instead of pretending success.
