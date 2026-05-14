# Architecture Note: CLI, Backend API, And Future Admin Frontend

## Short Answer

Yes, for implemented capabilities, because `ragcli` is API-first.

Implemented `ragcli` commands call FastAPI routes for auth, documents, retrieval, admin document operations, logs, jobs, and LightRAG graph reads. The CLI does not manage LightRAG deployments locally.

For future LightRAG deployment/domain administration, the same rule applies: if `ragcli` commands directly manage LightRAG deployments locally, then a future admin frontend cannot reuse those capabilities. A browser frontend cannot safely run local shell scripts, Docker commands, or edit local deployment manifests.

For frontend readiness, the backend must expose admin-only FastAPI routes for LightRAG domain/knowledge-base deployment, deletion, status, and configuration. Then:

```text
ragcli -> FastAPI API
frontend -> same FastAPI API
```

This makes the CLI and frontend two clients of the same control plane.

---

## Current Principle

Every real `ragcli` command mirrors a backend route.

That means this is the required model for future deployment commands:

```text
ragcli admin lightrag domain deploy
  -> POST /admin/lightrag/domains/{domain_id}/deploy
  -> backend deployment service
  -> local compose / deployment backend
```

Not this:

```text
ragcli lightrag domain deploy
  -> local shell/Docker logic directly
```

The backend should own authorization, state, audit logs, and operation status.

---

## Why This Matters

A local-only CLI implementation would create two systems:

```text
CLI path:
ragcli -> local scripts -> Docker/manifest

Future frontend path:
frontend -> ??? no equivalent backend routes
```

That creates duplicated logic and makes it hard to build an admin UI later.

An API-first implementation creates one shared system:

```text
CLI path:
ragcli -> FastAPI routes -> deployment service

Frontend path:
admin UI -> same FastAPI routes -> same deployment service
```

This keeps the code leaner long term.

---

## Recommended Future Direction

Add LightRAG deployment/deletion/status capabilities to `context_engine` in this order:

1. Backend admin API contract
2. Backend service layer
3. Storage/domain registry
4. Deployment backend implementation
5. Mirrored `ragcli admin lightrag ...` commands
6. Future frontend using same routes

---

## Future Command Shape

Use admin namespace because deployment is privileged:

```bash
ragcli admin lightrag domains list
ragcli admin lightrag domains create --name "AbleMed Manuals" --port 9621
ragcli admin lightrag domains show --domain-id kb_123
ragcli admin lightrag domains delete --domain-id kb_123

ragcli admin lightrag deployments deploy --domain-id kb_123
ragcli admin lightrag deployments start --domain-id kb_123
ragcli admin lightrag deployments stop --domain-id kb_123
ragcli admin lightrag deployments restart --domain-id kb_123
ragcli admin lightrag deployments recreate --domain-id kb_123
ragcli admin lightrag deployments status --domain-id kb_123
```

Shorter aliases are acceptable later, but the first implementation should be explicit.

---

## Future API Shape

```http
GET    /admin/lightrag/domains
POST   /admin/lightrag/domains
GET    /admin/lightrag/domains/{domain_id}
DELETE /admin/lightrag/domains/{domain_id}

POST /admin/lightrag/domains/{domain_id}/deploy
POST /admin/lightrag/domains/{domain_id}/start
POST /admin/lightrag/domains/{domain_id}/stop
POST /admin/lightrag/domains/{domain_id}/restart
POST /admin/lightrag/domains/{domain_id}/recreate
GET  /admin/lightrag/domains/{domain_id}/status

POST /admin/lightrag/domains/{domain_id}/regenerate
GET  /admin/lightrag/domains/{domain_id}/config
GET  /admin/lightrag/domains/{domain_id}/events
```

`events` and `logs` can be deferred if they introduce too much complexity.

---

## Backend Source Of Truth

Prefer:

```text
Database = source of truth for app/admin/frontend
Generated manifest/env/compose files = runtime artifacts
```

The backend should track domain records and deployment operation status.

A domain record should include at least:

```text
id
name
slug
base_url
port
status
health
created_by_user_id
created_at
updated_at
deployment_backend
external_engine
metadata_json
```

The manifest can still exist for compatibility with `easy-deploy-lightrag`, but it should not be the only source of truth for the multi-user app.

---

## Deployment Backend Strategy

For v1, use a small local deployment backend that adapts the working behavior from `easy-deploy-lightrag`.

Example structure:

```text
app/services/lightrag_deployment_service.py
app/services/deployment_backends/base.py
app/services/deployment_backends/local_compose.py
app/api/routes/admin_lightrag.py
app/storage/repositories/lightrag_domains.py
```

Keep Docker/script calls isolated to `local_compose.py`.

Do not put subprocess calls inside route handlers.

---

## Frontend Readiness Checklist

A future admin frontend should be able to:

- list knowledge bases/domains
- create a knowledge base/domain
- deploy/start/stop/recreate/delete it
- view health/status
- upload documents through existing admin upload routes
- see indexing/deployment jobs
- view graph/retrieval status
- never see raw secrets

That requires stable JSON responses from the backend.

---

## Security Rules

- Backend admin auth protects deployment routes.
- CLI does not decide who is admin.
- Secrets are masked in API and CLI output.
- Do not print `.env` contents.
- Do not expose container logs by default if they may contain secrets.
- Prefer explicit allowlisted config fields in responses.
- Deployment errors should be actionable but not leak internal secret paths or env values.

---

## Smallest Safe Future Phase 1

Do not start by wiring Docker.

Start with:

1. Add backend admin route skeletons for:
   - list domains
   - create domain
   - show domain
   - delete domain
2. Add minimal storage/repository for domain records.
3. Add route tests for admin vs non-admin.
4. Add CLI commands that mirror only those routes.
5. Add docs showing the API/CLI mapping.

After this is green, add deployment lifecycle operations.

---

## Bottom Line

The current CLI implementation already follows the API-first rule for supported commands. Future LightRAG deployment work must keep following it.

The correct future plan is not:

```text
Add LightRAG deployment logic to CLI
```

The correct future plan is:

```text
Add LightRAG deployment logic to backend admin API, then mirror those routes in CLI.
```

This is what makes the future frontend possible without rewriting the deployment system.
