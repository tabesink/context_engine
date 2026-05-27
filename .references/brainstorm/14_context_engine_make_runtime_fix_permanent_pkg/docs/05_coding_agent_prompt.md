# 05 — Coding Agent Prompt

You are working in `https://github.com/tabesink/context_engine.git`.

Goal: make the current temporary LightRAG/Postgres runtime fix permanent.

Context:
- A legacy LightRAG container `lightrag_fatigue` was failing with:
  `FATAL: password authentication failed for user "lightrag"; Role "lightrag" does not exist`.
- A manual runtime fix created role/database `lightrag`, granted privileges, enabled `vector`, and restarted the container.
- That made `http://127.0.0.1:9622/health` healthy.
- But this must become a repeatable code-level lifecycle behavior.
- A managed container `context_engine_lightrag_fatigue` is still separately failing due tokenizer DNS startup; fix that too.

Implement the permanent fix with low entropy:

1. Add explicit LightRAG Postgres settings:
   - `LIGHTRAG_STORAGE_BACKEND=postgres`
   - `LIGHTRAG_POSTGRES_PROVISIONING_MODE=per_domain`
   - `LIGHTRAG_POSTGRES_COMPAT_ENABLED=true`
   - compatibility db/user/password defaults: `lightrag`
   - tokenizer cache settings.

2. Fix `app/lightrag_deploy/compose.py`:
   - Do not render app runtime DB credentials for managed LightRAG domains.
   - Render per-domain credentials in per-domain mode.
   - Render `lightrag/lightrag` only in explicit compat mode.
   - Render `TIKTOKEN_CACHE_DIR`.

3. Add `app/lightrag_deploy/postgres_provisioner.py`:
   - idempotently create role/database/extensions/privileges.
   - create `vector` extension in each target DB.
   - create/attempt `age` extension if available.
   - support `ensure_for_domain()` and `ensure_legacy_compat()`.

4. Wire provisioner into:
   - domain create
   - regenerate
   - up
   - recreate
   - new repair endpoint.

5. Add:
   `POST /admin/lightrag/domains/{domain_id}/repair`

6. Fix runtime URL resolution:
   - socket mode uses `container_base_url`.
   - host mode uses `host_base_url`.
   - do not blindly trust persisted `base_url`.

7. Fix tokenizer DNS startup:
   - ensure LightRAG image contains required tokenizer cache.
   - generated env includes `TIKTOKEN_CACHE_DIR=/app/.cache/tiktoken`.
   - container startup should not require public DNS for tokenizer files.

8. Add tests:
   - env rendering
   - provisioner idempotency
   - repair lifecycle
   - registry runtime URL selection.

Acceptance:
- `docker compose down -v && docker compose up --build` can create/repair `fatigue` without manual SQL.
- No Postgres logs show `Role "lightrag" does not exist`.
- No `type "vector" does not exist` errors.
- Managed container health returns healthy.
- Upload -> worker ingest -> LightRAG status polling works.
