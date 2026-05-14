# CLI Implementation And Test Coverage

The CLI is built and maintained in vertical behavior slices. Each supported command should have a test that proves it calls the expected public backend route, handles authentication consistently, and renders stable JSON.

## Covered Slice 1: Session Lifecycle

Behavior covered in `tests/test_cli.py`:

- `login` posts email and password to `/auth/login`, stores the returned token, and does not print the token.
- `logout` clears stored credentials and succeeds without a backend call.
- `auth me` calls `GET /auth/me`.
- A protected command with no stored credentials exits with `auth_required`.
- Commands warn when the saved session base URL differs from the current root `--api-base-url`.

Acceptance:

- Passwords are not stored.
- Tokens are not printed.
- JSON output is valid JSON on success and failure.
- The saved session base URL is the source of truth for authenticated calls.

## Covered Slice 2: Documents And Retrieval

Behavior covered:

- `documents list --output json` calls `GET /documents` and wraps the list as `{documents: [...]}`.
- `documents show` calls `GET /documents/{document_id}`.
- `documents structure` calls `GET /documents/{document_id}/structure`.
- `documents page` calls `GET /documents/{document_id}/pages/{page_number}`.
- `documents retrieve` calls `POST /query/retrieve`.
- `documents answer` calls `POST /query/answer`.
- `query` calls `POST /query`.
- Query payloads include `query`, `mode`, `top_k`, `include_debug`, `allow_general_fallback`, and optional `document_ids`.
- Repeated `--document-id` values become a JSON array.
- Query payload construction is concentrated in `cli/query_payload.py` and validated through the backend `QueryRequest` schema so CLI field drift is caught close to the command layer.

Acceptance:

- Commands use only public backend routes.
- Retrieval modes match backend schema.
- Human output remains operator-friendly.
- JSON output remains stable for scripts.

## Covered Slice 3: Admin Documents, Logs, And Jobs

Behavior covered:

- `admin documents upload` sends multipart field `file` to `/admin/documents/upload`.
- `admin documents index` and `reindex` call current admin routes.
- `admin documents delete` renders the deleted document response.
- `admin documents list` calls `GET /admin/documents`.
- `admin audit-logs list` calls `GET /admin/audit-logs`.
- `admin query-logs list` calls `GET /admin/query-logs`.
- `jobs list`, `jobs status`, and `jobs retry` call current job routes.
- Backend admin failures surface through the same API error handling path without leaking tokens.

Acceptance:

- Admin commands do not duplicate authorization logic.
- File-read failures are local CLI errors.
- Backend API errors preserve code, message, and status where available.

## Covered Slice 4: LightRAG Graph Reads

Behavior covered:

- `lightrag graphs show` calls `GET /graphs` with `label`, `max_depth`, and `max_nodes`.
- `lightrag labels list` calls `GET /graph/label/list`.
- `lightrag labels popular` calls `GET /graph/label/popular`.
- `lightrag labels search` calls `GET /graph/label/search`.

Acceptance:

- The CLI does not call LightRAG directly.
- LightRAG disabled/upstream errors are rendered as backend API errors.
- JSON output preserves the backend response shape.

## Covered Slice 5: Full Surface Gap Handling

Behavior covered:

- Planned commands without backend routes return `not_supported_by_backend`.
- JSON mode returns a structured error.
- Human mode names the missing backend capability and points to `docs/cli_docs/api-contract.md`.

Acceptance:

- Gaps are explicit and test-covered.
- No fake local implementation substitutes for missing backend behavior.

## Refactor Rule

Refactor only while tests are green. Split modules when duplication or command growth justifies it, not before.
