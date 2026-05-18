# 3. Backend Module and API Plan

## 3.1 New Backend Module

Add:

```text
app/lightrag_deploy/
  __init__.py
  models.py
  settings.py
  paths.py
  manifest.py
  compose.py
  docker_runner.py
  health.py
  service.py
  errors.py
```

## 3.2 Module Responsibilities

| File | Responsibility |
|---|---|
| `models.py` | Pydantic/domain models: `LightRAGDomain`, `DomainStatus`, requests/responses. |
| `settings.py` | Adapts `app.core.config.Settings` into deployment-specific config. |
| `paths.py` | Resolves `.data/lightrag/...` paths and creates folder structures. |
| `manifest.py` | Atomic read/write of `domains.json`; validation; no Docker calls. |
| `compose.py` | Deterministic compose-file generation from manifest/settings; no subprocess calls. |
| `docker_runner.py` | Small command runner interface for `docker compose`; fakeable in tests. |
| `health.py` | HTTP health checks against running LightRAG domains. |
| `service.py` | Main orchestration use cases: create/list/show/up/down/recreate/remove/status. |
| `errors.py` | Typed errors converted to HTTP responses by route layer. |

## 3.3 Keep Existing Runtime Modules

Do not replace these:

```text
app/integrations/lightrag_remote_adapter.py
app/integrations/lightrag_domains.py
app/retrieval/lightrag_remote_engine.py
app/api/routes/lightrag.py
```

Instead, update `app/integrations/lightrag_domains.py` to read the same generated manifest if needed.

## 3.4 New Route File

Add:

```text
app/api/routes/lightrag_admin.py
```

Mount it in `app/main.py`.

## 3.5 Admin-Only Domain Control APIs

Prefix:

```text
/admin/lightrag/domains
```

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/admin/lightrag/domains` | Admin | List all configured domains with status/health. |
| `POST` | `/admin/lightrag/domains` | Admin | Create/register a new domain. |
| `GET` | `/admin/lightrag/domains/{domain_id}` | Admin | Show one domain, paths, status, health. |
| `POST` | `/admin/lightrag/domains/{domain_id}/up` | Admin | Start domain container. |
| `POST` | `/admin/lightrag/domains/{domain_id}/down` | Admin | Stop domain container. |
| `POST` | `/admin/lightrag/domains/{domain_id}/recreate` | Admin | Recreate domain container. |
| `POST` | `/admin/lightrag/domains/{domain_id}/regenerate` | Admin | Regenerate domain env + compose without starting. |
| `DELETE` | `/admin/lightrag/domains/{domain_id}` | Admin | Archive/remove domain by default. |
| `DELETE` | `/admin/lightrag/domains/{domain_id}?permanent=true` | Admin + config | Permanent delete only if explicitly enabled. |

## 3.6 User-Safe Domain Read API

Normal users need domain list for query selection.

Add a separate read-only route:

```text
GET /lightrag/domains
```

Auth:

```text
authenticated user
```

Response should include only user-safe information:

```json
{
  "domains": [
    {
      "id": "fatigue",
      "display_name": "Fatigue Manuals",
      "base_url": null,
      "is_healthy": true,
      "is_default": false
    }
  ]
}
```

Do not expose:

- env paths
- secrets
- Docker command details
- host file paths if not needed
- container names unless harmless

## 3.7 Request/Response Models

Suggested schemas:

```python
class LightRAGDomainCreateRequest(BaseModel):
    domain_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{1,62}$")
    display_name: str | None = None
    host_port: int | None = Field(default=None, ge=1, le=65535)
    make_default: bool = False

class LightRAGDomainResponse(BaseModel):
    id: str
    display_name: str
    host_port: int
    container_port: int
    base_url: str
    service_name: str
    container_name: str
    status: str
    is_healthy: bool | None = None
    created_at: datetime
    updated_at: datetime

class LightRAGDomainRemoveResponse(BaseModel):
    id: str
    archived: bool
    archive_path: str | None
    permanent: bool
```

## 3.8 Service Methods

`app/lightrag_deploy/service.py` should expose a small class:

```python
class LightRAGDomainService:
    def list_domains(self) -> list[LightRAGDomain]: ...
    def get_domain(self, domain_id: str) -> LightRAGDomain: ...
    def create_domain(self, request: LightRAGDomainCreateRequest) -> LightRAGDomain: ...
    def regenerate(self, domain_id: str | None = None) -> None: ...
    def up(self, domain_id: str) -> LightRAGDomainOperationResult: ...
    def down(self, domain_id: str) -> LightRAGDomainOperationResult: ...
    def recreate(self, domain_id: str) -> LightRAGDomainOperationResult: ...
    def remove(self, domain_id: str, *, permanent: bool = False) -> LightRAGDomainRemoveResponse: ...
    def status(self, domain_id: str) -> LightRAGDomainStatus: ...
```

Keep service methods boring and easy to follow.

## 3.9 Route Layer Rules

Routes should:

- parse request
- enforce `require_admin` or authenticated user
- call `LightRAGDomainService`
- map typed errors to HTTP exceptions
- return schema objects

Routes should not:

- build Docker commands
- write files directly
- know compose syntax
- implement deletion logic
- call LightRAG HTTP runtime APIs directly except through service/health helpers

## 3.10 Config Guard

If `LIGHTRAG_DEPLOY_ENABLED=false`, admin deployment routes should return:

```text
403 or 400: LightRAG deployment is disabled
```

Recommendation:

- Use `400` when feature disabled due config.
- Use `403` when user lacks admin rights.

## 3.11 Audit Logging

Every admin domain operation should write an audit event:

```text
lightrag.domain.created
lightrag.domain.started
lightrag.domain.stopped
lightrag.domain.recreated
lightrag.domain.archived
lightrag.domain.deleted_permanently
lightrag.domain.regenerated
```

Metadata should include:

```json
{
  "domain_id": "fatigue",
  "host_port": 9622,
  "service_name": "lightrag_fatigue"
}
```

## 3.12 System Status Integration

If there is or will be an admin system status endpoint, include:

- deployment feature enabled/disabled
- manifest path exists/readable
- compose file exists
- Docker executable reachable
- Docker socket/daemon reachable
- configured domains count
- unhealthy domains count
- missing path warnings
