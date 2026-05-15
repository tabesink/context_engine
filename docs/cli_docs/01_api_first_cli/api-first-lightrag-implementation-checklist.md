# Implementation Checklist: API-First LightRAG Admin Deployment

## Goal

Track future LightRAG knowledge-base/domain deployment capabilities for `context_engine` in a way that both `ragcli` and a future admin frontend can use.

Current code already supports remote LightRAG retrieval, upload forwarding, and graph proxy reads. It does not implement backend admin routes for deploying, starting, stopping, deleting, or configuring LightRAG domains. Those future commands must remain backend-first.

---

## Phase 0: Existing Contracts

- [x] `ragcli` commands mirror backend routes.
- [x] Existing `ragcli` auth/session behavior is implemented.
- [x] Existing admin auth dependency is `require_admin`.
- [x] Existing job/status route pattern is implemented under `/jobs`.
- [x] Existing document upload and retrieval routes are implemented.
- [x] Current LightRAG retrieval/upload/graph boundary is `LightRAGRemoteAdapter`.
- [ ] `easy-deploy-lightrag` domain lifecycle features are not part of the current codebase and must be re-evaluated before implementation.

---

## Future Phase 1: Backend API Skeleton

Create route file:

```text
app/api/routes/admin_lightrag.py
```

Add routes:

```http
GET    /admin/lightrag/domains
POST   /admin/lightrag/domains
GET    /admin/lightrag/domains/{domain_id}
DELETE /admin/lightrag/domains/{domain_id}
```

Future tests:

- [ ] Admin can list domains.
- [ ] Admin can create domain.
- [ ] Admin can show domain.
- [ ] Admin can delete domain.
- [ ] Normal user receives `403`.
- [ ] Unauthenticated user receives auth error.
- [ ] JSON response shapes are stable.

---

## Future Phase 2: Domain Registry

Add repository/model for LightRAG domains or knowledge bases.

Minimum fields:

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

Future tests:

- [ ] Duplicate slug rejected.
- [ ] Invalid slug rejected.
- [ ] Invalid port rejected.
- [ ] Domain create returns stable frontend-friendly JSON.
- [ ] Domain delete does not leak runtime secrets.

---

## Future Phase 3: Deployment Service Boundary

Create service:

```text
app/services/lightrag_deployment_service.py
```

Create local backend adapter:

```text
app/services/deployment_backends/local_compose.py
```

Routes to add:

```http
POST /admin/lightrag/domains/{domain_id}/deploy
POST /admin/lightrag/domains/{domain_id}/start
POST /admin/lightrag/domains/{domain_id}/stop
POST /admin/lightrag/domains/{domain_id}/restart
POST /admin/lightrag/domains/{domain_id}/recreate
GET  /admin/lightrag/domains/{domain_id}/status
```

Future tests:

- [ ] Route handlers do not call subprocess directly.
- [ ] Deployment backend is mocked.
- [ ] Docker unavailable returns stable error.
- [ ] Long operation returns `job_id` if async.
- [ ] Status response is stable for frontend.

---

## Future Phase 4: Adapt `easy-deploy-lightrag`

Port/adapt only what is needed:

- [ ] domain manifest generation
- [ ] env generation with masked output
- [ ] compose file generation or use existing compose template
- [ ] deploy/start/stop/recreate behavior
- [ ] status/health checks
- [ ] archive/delete behavior

Do not port:

- [ ] unrelated chat CLI behavior
- [ ] duplicate retrieval logic
- [ ] local-only UX that cannot be represented by backend API
- [ ] large shell scripts if small Python helpers are clearer

---

## Future Phase 5: CLI Mirrors Backend Routes

Add commands only after backend routes exist:

```bash
ragcli admin lightrag domains list
ragcli admin lightrag domains create --name NAME --port PORT
ragcli admin lightrag domains show --domain-id DOMAIN_ID
ragcli admin lightrag domains delete --domain-id DOMAIN_ID

ragcli admin lightrag deployments deploy --domain-id DOMAIN_ID
ragcli admin lightrag deployments start --domain-id DOMAIN_ID
ragcli admin lightrag deployments stop --domain-id DOMAIN_ID
ragcli admin lightrag deployments restart --domain-id DOMAIN_ID
ragcli admin lightrag deployments recreate --domain-id DOMAIN_ID
ragcli admin lightrag deployments status --domain-id DOMAIN_ID
```

Future tests:

- [ ] Every command calls the expected backend route.
- [ ] CLI does not call Docker/subprocess.
- [ ] CLI does not require local LightRAG files.
- [ ] Admin `403` is rendered consistently.
- [ ] JSON output is stable.
- [ ] Secrets are never printed.

---

## Future Phase 6: Frontend Readiness

- [ ] API responses are UI-friendly.
- [ ] Domain create response includes domain object.
- [ ] Deploy/start/stop responses include operation or job.
- [ ] Status response includes health, base URL, and last checked time.
- [ ] Config response masks secrets.
- [ ] OpenAPI docs are readable.
- [ ] Errors are stable and actionable.

---

## Explicit Deferrals

- [ ] Kubernetes deployment
- [ ] multi-host orchestration
- [ ] cloud provider deployment
- [ ] frontend implementation
- [ ] live log streaming
- [ ] secret rotation UI
- [ ] graph editing
- [ ] per-user non-admin deployment permissions
- [ ] complex retrieval profiles

---

## Definition Of Done For Future Deployment Work

- [ ] Backend routes exist for the implemented operations.
- [ ] CLI commands mirror those routes.
- [ ] Future frontend can use the same route contracts.
- [ ] Tests do not require Docker or live LightRAG.
- [ ] No secrets are printed.
- [ ] Existing document/retrieval/admin CLI behavior remains unchanged.
- [ ] LightRAG retrieval remains behind the HTTP adapter.
