# Junior Dev Implementation Plan

## Goal

Remove dual LightRAG domain behavior. Context Engine must resolve LightRAG runtime connection details only from the LightRAG Domain Registry at `.data/lightrag/domains.json` or the configured `LIGHTRAG_DOMAIN_REGISTRY` path.

## Expected Contract

- `GET /lightrag/domains` lists the registered domains for frontend dropdowns.
- `POST /admin/documents/upload` requires `lightrag_domain_id`.
- `POST /retrieve` requires `lightrag_domain_id`.
- Graph and workspace-tree routes validate `{domain_id}` against the same registry.
- Unknown domain ids fail before any LightRAG HTTP call.
- No code path falls back to `LIGHTRAG_BASE_URL` or `LIGHTRAG_DOMAIN`.

## Implementation Slices

1. Add `app/services/lightrag_domain_registry.py`.
   - Parse the registry payload.
   - Return user-safe summaries for dropdowns.
   - Return runtime connection data (`id`, `base_url`, optional `api_key`) for adapters.
   - Raise clear errors for missing id, unknown domain, unavailable status, or missing `base_url`.

2. Replace fallback resolution.
   - Refactor `app/integrations/lightrag_domains.py` to use the registry service.
   - Refactor `LightRAGRemoteAdapter.for_domain()` so it accepts only an explicit domain id.
   - Do not use `settings.lightrag_base_url`, `settings.lightrag_api_key`, or `settings.lightrag_domain` for runtime resolution.

3. Make frontend-facing requests explicit.
   - Upload should return `400` when `lightrag_domain_id` is missing.
   - Retrieve should return `400` when `lightrag_domain_id` is missing.
   - Unknown domains should return `404`.

4. Centralize validation.
   - Replace manual manifest parsing in `DocumentService`.
   - Validate graph routes before proxying to LightRAG.
   - Use the same registry contract for workspace tree.
   - Keep `/lightrag/domains` user-safe: no paths, container names, ports, database names, or provider settings.

5. Update configuration and docs.
   - Use `LIGHTRAG_DOMAIN_REGISTRY` as the normal runtime config.
   - Keep deployment tooling optional, but make it write to the same registry path.
   - Update examples and tests to stop relying on `LIGHTRAG_BASE_URL`.

## Verification

Run:

```bash
uv run pytest tests/test_lightrag_remote_adapter.py tests/test_lightrag_deploy_settings.py tests/test_api.py -q
```

Then run the full suite if the focused tests pass.
