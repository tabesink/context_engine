# Backend Test Plan

## Route surface tests

Assert these exist:

```text
GET    /admin/lightrag/domains
POST   /admin/lightrag/domains
GET    /admin/lightrag/domains/{domain_id}
POST   /admin/lightrag/domains/{domain_id}/up
POST   /admin/lightrag/domains/{domain_id}/down
DELETE /admin/lightrag/domains/{domain_id}
GET    /lightrag/domains
```

Assert these are removed or return `410 Gone` if compatibility mode is chosen:

```text
POST   /admin/lightrag/domains/{domain_id}/repair
POST   /admin/lightrag/domains/{domain_id}/recreate
POST   /admin/lightrag/domains/{domain_id}/regenerate
POST   /admin/lightrag/domains/{domain_id}/purge-preview
DELETE /admin/lightrag/domains/{domain_id}/purge
```

## Create tests

- Create accepts domain ID, display name, embedding profile, host port.
- Create rejects or ignores unknown `start` depending on strictness policy.
- Create rejects or ignores retrieval default fields depending on strictness policy.
- Create writes manifest.
- Create writes initial env/compose if still part of create.
- Create does not call Docker runner.
- Create returns status configured/stopped, not running.

## Start tests

- Start refreshes domain env.
- Start writes Compose.
- Start provisions Postgres if enabled.
- Start calls Docker build/up.
- Start probes health.
- Start persists running/unhealthy/error.
- Start uses current provider secret value.
- Start uses domain embedding snapshot.
- Start uses retrieval defaults from backend settings.

## Stop tests

- Stop calls Docker stop.
- Stop persists stopped/error.

## Delete tests

- Delete removes domain from active manifest.
- Delete rewrites Compose.
- Delete moves runtime root to deleted/archive location.
- Delete preserves local document rows.
- Delete preserves document structure rows.
- Delete blocks future upload/retrieval/status for that domain.

## Env tests

- `domain.env` contains retrieval defaults from settings.
- `domain.env` contains current provider secret values.
- Manifest does not contain provider secret values.
- API response does not contain provider secret values.
