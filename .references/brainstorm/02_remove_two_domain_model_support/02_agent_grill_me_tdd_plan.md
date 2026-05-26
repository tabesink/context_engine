# Agent Grill-Me + TDD Plan

## Decision Checklist

Before coding, lock these answers:

- Missing `lightrag_domain_id` returns `400`.
- Unknown registered-domain lookup returns `404`.
- Unavailable statuses (`stopped`, `unhealthy`, `archived`, `error`) return `400`.
- The only runtime domain source is `LIGHTRAG_DOMAIN_REGISTRY`.
- Deployment tools are operational helpers; they are not a separate domain mode.

## TDD Tracer Bullets

Work vertically. Do not write all tests first.

1. RED: retrieve without `lightrag_domain_id` fails.
   GREEN: validate the field in the retrieval service and return `400`.

2. RED: retrieve with an unknown domain fails before LightRAG is called.
   GREEN: add registry validation before retrieval strategy execution.

3. RED: graph proxy with an unknown domain fails before adapter creation.
   GREEN: validate `{domain_id}` in graph proxy helpers.

4. RED: upload without `lightrag_domain_id` fails.
   GREEN: remove default-domain fallback in `DocumentService`.

5. RED: upload with an unknown domain fails through the same registry.
   GREEN: replace manual manifest parsing with `LightRAGDomainRegistry`.

6. RED: resolver no longer succeeds when only `LIGHTRAG_BASE_URL` exists.
   GREEN: resolve runtime connection details exclusively from the registry.

7. RED: `/lightrag/domains` exposes only dropdown-safe fields.
   GREEN: list domains via the registry summary API.

## Refactor Pass

After the tracer bullets are green:

- Remove hidden default adapter creation from `LightRAGRemoteRetrievalEngine`.
- Keep direct `LightRAGRemoteAdapter(...)` construction for tests and low-level adapter usage only.
- Make deployment settings write to the same registry path.
- Update docs and `.env` examples to explain `LIGHTRAG_DOMAIN_REGISTRY`.

## Guardrails

- Tests should exercise public HTTP APIs wherever possible.
- Do not mock internal registry methods when an API-level test can prove the behavior.
- Mock LightRAG HTTP calls only to prove the backend does not reach upstream for invalid domains.
- Keep registry entries lean in examples: `id`, `display_name`, `base_url`, optional `api_key`, `status`, `is_default`, `is_healthy`.
