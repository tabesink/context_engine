# Preserve List

These are architectural choices that should be preserved during cleanup unless there is strong evidence and tests proving a better path.

## Preserve auth and admin boundaries

- Admin-only upload and LightRAG domain CRUD must remain backend-enforced.
- Frontend role checks are convenience, not security.
- Do not move permission decisions into UI-only logic.

## Preserve LightRAG boundary

- Keep LightRAG as a runtime/integration boundary rather than mixing LightRAG internals directly into route handlers.
- Keep HTTP/runtime adapter semantics clear.
- Do not hide Docker/Compose/provisioning errors behind vague messages.

## Preserve explicit destructive-operation safety

- Keep purge-preview before purge.
- Keep explicit confirmation for purge.
- Keep audit logging for destructive lifecycle actions.

## Preserve document registry and job distinction

- Document identity/status and job execution attempts are different concepts.
- Do not collapse jobs into documents unless retry/failure semantics are preserved.

## Preserve canonical evidence contract

- Retrieval evidence should feed chat, workspace tree, context stream, and source navigation consistently.
- Avoid separate “source”, “citation”, “context item”, and “workspace item” models if they represent the same thing.

## Preserve tests as cleanup guardrails

The repository appears to have a broad test suite around LightRAG deployment, retrieval, processing status, rich navigation, and workspace context. Cleanup should add to this suite, not bypass it.

## Preserve deployment clarity

- Keep `.env.example` and LightRAG env examples aligned with actual config.
- Keep Docker/local development path working.
- Do not change ports, volumes, commands, or storage paths without updating docs.

## Preserve boring explicit architecture

The goal is not to replace direct, readable code with abstract factories or frameworks. Extract only when extraction removes duplicated mental models or repeated risky code.
