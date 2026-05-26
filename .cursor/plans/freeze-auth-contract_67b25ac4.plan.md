---
name: freeze-auth-contract
overview: Freeze the authentication contract to strict username/password login with `/auth/*` routes and migrate the web client to Bearer-token flow without introducing `/api/v1/auth/*` aliases.
todos:
  - id: freeze-login-schema
    content: Remove legacy email login support and enforce strict LoginRequest(username,password).
    status: completed
  - id: migrate-web-auth-flow
    content: Update web client auth endpoints and request/auth-store flow to Bearer token with /auth/* routes.
    status: completed
  - id: align-auth-tests
    content: Update and expand tests to assert frozen auth contract and protected endpoint behavior.
    status: completed
  - id: update-auth-docs
    content: Document frozen contract and explicitly remove /api/v1/auth alias expectations.
    status: completed
isProject: false
---

# Freeze Auth Contract and Align Web Client

## Objective
Stabilize on a single auth contract across backend and UI:
- `POST /auth/login` with `{ username, password }`
- `GET /auth/me` with `Authorization: Bearer <access_token>`
- Login response `{ access_token, token_type: "bearer" }`
- No `/api/v1/auth/*` compatibility routes

## Current State (validated)
- Backend routes and dependency flow already live under [`/data/home/tkodippili/Desktop/localTest_context_engine/app/api/routes/auth.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/api/routes/auth.py) and [`/data/home/tkodippili/Desktop/localTest_context_engine/app/api/deps.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/api/deps.py).
- Request schema still allows legacy `email` via validator in [`/data/home/tkodippili/Desktop/localTest_context_engine/app/schemas/auth.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/schemas/auth.py).
- Web client currently hardcodes `/api/v1/auth/*` in [`/data/home/tkodippili/Desktop/localTest_context_engine/client/src/lib/api/auth.ts`](/data/home/tkodippili/Desktop/localTest_context_engine/client/src/lib/api/auth.ts).

## Implementation Plan

### 1) Freeze backend login schema to strict username/password
- Update [`/data/home/tkodippili/Desktop/localTest_context_engine/app/schemas/auth.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/schemas/auth.py):
  - Remove `email` field and legacy normalization validator.
  - Keep `username` required with existing bounds.
- Keep route surface unchanged in [`/data/home/tkodippili/Desktop/localTest_context_engine/app/api/routes/auth.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/api/routes/auth.py): only `/auth/login` and `/auth/me`.

### 2) Migrate web client auth paths and token handling
- Refactor [`/data/home/tkodippili/Desktop/localTest_context_engine/client/src/lib/api/auth.ts`](/data/home/tkodippili/Desktop/localTest_context_engine/client/src/lib/api/auth.ts):
  - Replace `/api/v1/auth/login` and `/api/v1/auth/me` with `/auth/login` and `/auth/me`.
  - Remove calls to non-existent backend auth actions (`/logout`, `/change-password`) or convert to client-local operations where appropriate.
- Update API client/request layer in [`/data/home/tkodippili/Desktop/localTest_context_engine/client/src/lib/api/client.ts`](/data/home/tkodippili/Desktop/localTest_context_engine/client/src/lib/api/client.ts):
  - Inject Bearer header from auth state/token storage for protected calls.
  - Stop relying on cookie-only behavior for auth (do not depend on `credentials: "include"` for session auth).
- Update state wiring in [`/data/home/tkodippili/Desktop/localTest_context_engine/client/src/stores/auth-store.ts`](/data/home/tkodippili/Desktop/localTest_context_engine/client/src/stores/auth-store.ts):
  - Handle login as token acquisition first, then hydrate user via `/auth/me`.
  - Persist and clear token consistently.

### 3) Align tests to frozen contract
- Update API tests in [`/data/home/tkodippili/Desktop/localTest_context_engine/tests/test_api.py`](/data/home/tkodippili/Desktop/localTest_context_engine/tests/test_api.py):
  - Change login helper payloads from `email` to `username`.
  - Add direct auth contract tests for:
    - successful login shape (`access_token`, `token_type == "bearer"`)
    - rejection of missing/invalid credentials
    - `/auth/me` success with Bearer token
    - `/auth/me` rejection with missing/invalid token
- Adjust any CLI/client tests that still post `email` (e.g. [`/data/home/tkodippili/Desktop/localTest_context_engine/tests/test_cli_api_client.py`](/data/home/tkodippili/Desktop/localTest_context_engine/tests/test_cli_api_client.py)).

### 4) Document contract and remove ambiguity
- Update deployment and contract docs:
  - [`/data/home/tkodippili/Desktop/localTest_context_engine/docs/deployment.md`](/data/home/tkodippili/Desktop/localTest_context_engine/docs/deployment.md)
  - [`/data/home/tkodippili/Desktop/localTest_context_engine/.env.example`](/data/home/tkodippili/Desktop/localTest_context_engine/.env.example) (if frontend env examples need auth/base-path clarification)
- Explicitly state there is no `/api/v1/auth/*` alias contract.

## Validation
- Backend tests for auth and protected endpoints pass.
- Frontend login/logout/session bootstrap path works end-to-end against backend `/auth/*` only.
- Confirm all protected frontend requests include `Authorization: Bearer <access_token>`.
- Confirm no remaining `/api/v1/auth/` references in active client/backend codepaths.

## Out of Scope
- Adding server-side `/auth/logout` or `/auth/change-password` endpoints.
- Introducing dual routing (`/auth/*` plus `/api/v1/auth/*`).