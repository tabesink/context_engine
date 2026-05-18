# API-First CLI Development Plan

## Goal

Maintain `context-engine` as a thin API client for every stable backend capability that operators need. The FastAPI backend remains the source of truth for auth, permissions, retrieval, LightRAG behavior, deployment state, and validation.

This document now records the implemented API-first CLI shape and the remaining future work. New CLI behavior should still be added with vertical TDD slices.

```text
context-engine -> FastAPI API -> backend services
future admin UI -> same FastAPI API -> same backend services
```

## Current State

The CLI calls backend routes for:

- auth/session commands
- document reads and retrieval
- document-scoped query filters through repeated `--document-id`
- admin document operations
- admin audit and query logs
- jobs
- LightRAG graph and label read commands

Planned command groups continue to return stable `not_supported_by_backend` errors until matching backend routes exist.

Remaining API-first gap:

- LightRAG domain/deployment administration is not implemented in backend routes or CLI commands. The CLI must not shell out to Docker or manage deployment manifests directly.

## Public Interface Direction

Prefer explicit commands that make the backend route obvious:

```bash
context-engine lightrag graphs show --label LABEL
context-engine lightrag labels list
context-engine lightrag labels popular --limit 20
context-engine lightrag labels search --query TEXT --limit 20

context-engine documents retrieve --query TEXT --document-id DOC_ID
context-engine documents answer --query TEXT --document-id DOC_ID
context-engine query --query TEXT --document-id DOC_ID
```

For future deployment and domain lifecycle work, keep the admin namespace from the LightRAG architecture note:

```bash
context-engine admin lightrag domains list
context-engine admin lightrag domains create --name NAME --port PORT
context-engine admin lightrag domains show --domain-id DOMAIN_ID
context-engine admin lightrag domains delete --domain-id DOMAIN_ID

context-engine admin lightrag deployments deploy --domain-id DOMAIN_ID
context-engine admin lightrag deployments status --domain-id DOMAIN_ID
```

Short aliases can come later. The first implementation should favor clear route parity and stable automation output.

## TDD Execution Model

Use the project TDD skill and work one behavior at a time:

```text
RED: add one behavior test through the CLI public interface
GREEN: add the smallest CLI/API-client change that passes
REFACTOR: only after green, preserving public JSON and human output
```

Tests should verify behavior through public interfaces. Prefer CLI tests that assert the requested backend path, method, parameters, auth behavior, and rendered JSON/human output. Add API tests only when backend behavior or route contracts change.

Likely test targets:

- `tests/test_cli.py` for command behavior and route parity.
- `tests/test_api.py` for backend route contracts and auth/error behavior.
- `tests/test_lightrag_remote_adapter.py` when LightRAG proxy behavior changes.

## Implemented Phase 0: Confirm Contracts

Before changing behavior, confirm and document the public contract for the slice being implemented.

Acceptance:

- The intended command shape is listed in `docs/cli_docs/api-contract.md`.
- JSON output examples include stable field names for automation.
- Unsupported commands still return structured `not_supported_by_backend` errors.
- No command stores passwords, prints tokens, or infers admin permissions locally.

## Implemented Phase 1: LightRAG Graph Read Commands

Read-only LightRAG graph access is implemented because the backend routes exist.

Target route mapping:

| Command | Backend | Role |
| --- | --- | --- |
| `context-engine lightrag graphs show --label LABEL` | `GET /graphs?label=LABEL` | authenticated |
| `context-engine lightrag labels list` | `GET /graph/label/list` | authenticated |
| `context-engine lightrag labels popular --limit N` | `GET /graph/label/popular?limit=N` | authenticated |
| `context-engine lightrag labels search --query TEXT --limit N` | `GET /graph/label/search?q=TEXT&limit=N` | authenticated |

Covered behavior:

1. `context-engine lightrag labels list` calls `GET /graph/label/list`.
2. `context-engine lightrag graphs show` calls `GET /graphs`.
3. `context-engine lightrag labels popular` calls `GET /graph/label/popular`.
4. `context-engine lightrag labels search` calls `GET /graph/label/search`.

Acceptance:

- CLI commands do not call LightRAG directly.
- Auth/session handling follows existing CLI patterns.
- LightRAG disabled or upstream errors are rendered through the existing error contract.
- Human output is useful for operators; JSON output preserves the backend response shape.

## Implemented Phase 2: Document-Scoped Query Filters

The CLI exposes the API `document_ids` request capability on query commands.

Target commands:

```bash
context-engine documents retrieve --query TEXT --document-id DOC_ID
context-engine documents retrieve --query TEXT --document-id DOC1 --document-id DOC2
context-engine documents answer --query TEXT --document-id DOC_ID
context-engine query --query TEXT --document-id DOC_ID
```

Covered behavior:

1. `documents retrieve --document-id DOC_ID` includes `document_ids`.
2. `documents answer --document-id DOC_ID` includes `document_ids`.
3. `query --document-id DOC_ID` includes `document_ids`.
4. Repeated `--document-id` values produce an array.

Acceptance:

- Existing query commands without `--document-id` keep their current request shape.
- Repeated `--document-id` values produce a JSON array in the request body.
- JSON and human output behavior remains unchanged.

## Implemented Phase 3: Admin Observability Parity

CLI coverage exists for stable admin observability routes.

```bash
context-engine admin audit-logs list
context-engine admin query-logs list
```

Acceptance:

- Non-admin responses are rendered consistently with existing admin command errors.
- Pagination/filter flags mirror backend parameters instead of inventing local behavior.
- Sensitive fields are omitted or masked by backend responses before CLI rendering.

## Future Phase 4: API-First LightRAG Deployment

For LightRAG domain deployment, follow `docs/cli_docs/api_first_cli/api-first-lightrag-implementation-checklist.md`.

The key rule remains that deployment commands wait for backend admin routes. The CLI must not shell out to Docker, edit local manifests, or run `easy-deploy-lightrag` directly.

Expected order:

1. Backend admin API skeleton.
2. Domain registry or repository.
3. Deployment service boundary.
4. Local deployment backend adapter.
5. Mirrored `context-engine admin lightrag ...` commands.
6. Frontend-ready JSON and OpenAPI documentation.

Acceptance:

- Route handlers do not call subprocess directly.
- CLI commands mirror backend routes.
- Tests do not require Docker or a live LightRAG service.
- Secrets are never printed in API or CLI output.

## Ongoing Phase 5: Contract And Gap Handling

After each vertical slice, update the docs that describe the public contract.

Required updates:

- `docs/cli_docs/api-contract.md` shows each supported command and backend route.
- `docs/cli_docs/commands.md` includes operator examples for new commands.
- `docs/cli_docs/security-and-output.md` is updated if output or error shapes change.
- Planned surfaces remain marked as `backend gap` until real backend routes exist.

Acceptance:

- Docs distinguish supported commands from future surface area.
- `not_supported_by_backend` remains the behavior for commands without backend contracts.
- The CLI stays a client of the API, not a second implementation of backend behavior.

## Definition Of Done

- New behavior is covered by vertical TDD slices through public interfaces.
- Every real command maps to a documented backend route.
- JSON output is stable enough for scripts and a future frontend.
- Human output is concise and operationally useful.
- Auth, admin checks, validation, retrieval, LightRAG, and deployment state remain backend-owned.
- Existing CLI behavior remains unchanged except for the documented additions.
