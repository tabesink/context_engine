# CLI TDD Build Plan

Build the CLI in vertical slices. Each slice starts with one behavior test through a public interface, then the smallest implementation to pass it.

## Slice 1: Session Lifecycle

Behavior tests:

- `login` posts email and password to `/auth/login`, stores the returned token, and does not print the token.
- `logout` clears stored credentials and succeeds when no backend call is needed.
- A protected command with no stored credentials exits with `auth_required`.

Acceptance:

- Passwords are not stored.
- Tokens are not printed.
- JSON output is valid JSON on success and failure.

## Slice 2: Documents And Retrieval

Behavior tests:

- `documents list --output json` calls `GET /documents` and wraps the list as `{documents: [...]}`.
- `documents show` calls `GET /documents/{document_id}`.
- `documents structure` calls `GET /documents/{document_id}/structure`.
- `documents page` calls `GET /documents/{document_id}/pages/{page_number}`.
- `documents retrieve` calls `POST /query/retrieve` with `query`, `mode`, and `top_k`.
- `documents answer` calls `POST /query/answer`.

Acceptance:

- Commands use only public backend routes.
- Retrieval modes match backend schema.
- Human output is readable, JSON output is stable.

## Slice 3: Admin Documents And Jobs

Behavior tests:

- `admin documents upload` sends multipart field `file` to `/admin/documents/upload`.
- `admin documents index` and `reindex` return a `job_id`.
- `admin documents delete` renders the deleted document response.
- `jobs list`, `jobs status`, and `jobs retry` call current job routes.
- Normal-user admin failures surface backend `403` errors without leaking tokens.

Acceptance:

- Admin commands do not duplicate authorization logic.
- File-read failures are local CLI errors.
- Backend API errors preserve code, message, and status where available.

## Slice 4: Full Surface Gap Handling

Behavior tests:

- Planned commands without backend routes return `not_supported_by_backend`.
- JSON mode returns a structured error.
- Human mode names the missing backend capability and suggests checking `docs/cli_docs/api-contract.md`.

Acceptance:

- Gaps are explicit and test-covered.
- No fake local implementation substitutes for missing backend behavior.

## Refactor Rule

Refactor only while tests are green. Split modules when duplication or command growth justifies it, not before.
