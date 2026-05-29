# Backend Touchpoints

This file tells the coding agent where to look and what to change.

## Known verified files

```text
app/storage/tables.py
app/domain/models.py
migrations/alembic/versions/
```

## Search map

Run these commands from repo root:

```bash
rg "JobRow|JobStatus|jobs|document_id" app tests migrations
rg "LightRAGDomainLifecycleRow|lightrag_domain_lifecycle|domain_lifecycle|domain_id" app tests migrations
rg "block_ids|child_section_ids|asset_ids" app tests migrations
rg "ai_model_settings|AIModelSettingsRow" app tests migrations
```

## Expected backend layers to inspect

Exact file names may differ, so search by symbol rather than assuming.

```text
app/storage/
  SQLAlchemy rows
  repositories
  database session handling

app/domain/
  Pydantic/domain models
  enum values
  service contracts

app/api/ or app/routes/
  FastAPI routers for documents, domains, jobs, providers

app/services/
  ingestion/indexing orchestration
  LightRAG domain lifecycle orchestration
  provider settings

app/workers/ or app/jobs/
  background processing
  status transitions
```

## Refactor rule

Do not let route handlers directly encode state transition rules.

Prefer:

```text
Route -> Service -> Repository -> SQLAlchemy Row
```

Bad:

```text
Route sets documents.status, jobs.status, and domain metadata independently.
```

Good:

```text
Service starts operation.
Service updates operation status.
Service rolls up document/domain current status through one helper.
Repository persists state.
Audit logger records immutable event.
```

## Suggested service methods

```python
class OperationService:
    async def create_operation(...): ...
    async def start_operation(...): ...
    async def succeed_operation(...): ...
    async def fail_operation(...): ...
    async def list_operations(...): ...

class DomainService:
    async def create_domain(...): ...
    async def start_domain(...): ...
    async def stop_domain(...): ...
    async def delete_domain(...): ...
    async def list_domains(...): ...

class DocumentStructureService:
    async def build_document_outline(...): ...
    async def build_section_tree(...): ...
    async def list_assets_for_block(...): ...
```

## Rollup helpers

Centralize these rules:

```python
def document_status_from_operation(operation_status: str) -> str:
    ...

def domain_state_from_operation(operation_type: str, operation_status: str) -> str:
    ...
```

Do not duplicate these mappings across routers, workers, and frontend polling code.
