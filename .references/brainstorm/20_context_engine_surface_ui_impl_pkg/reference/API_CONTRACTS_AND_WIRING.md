# API Contracts and Wiring Plan

## Backend ownership model

Context Engine should expose normalized status contracts. The frontend should not parse raw LightRAG status payloads.

### Sources to join

| Source | Responsibility |
|---|---|
| Document registry | canonical document identity, domain ownership, document lifecycle |
| Job system | queued/running/failed/completed app-side operations |
| LightRAG domain registry/control plane | domain runtime config, port/base URL, active/archived state |
| LightRAG status adapter | backend-only status snapshots from LightRAG |
| Docker/health probe | ephemeral runtime reachability |

## Suggested backend modules

```txt
app/integrations/lightrag/processing_status_adapter.py
app/services/processing_status_service.py
app/schemas/processing_status.py
app/api/routes/processing_status.py
```

If the codebase already has equivalent modules, extend them instead of creating duplicates.

## Normalized schemas

### DocumentProcessingStatusResponse

```python
class DocumentProcessingStatusResponse(BaseModel):
    document_id: str
    domain_id: str
    job_id: str | None = None
    status: Literal[
        "queued", "uploading", "pending", "processing", "indexed",
        "failed", "cancelled", "archived", "unknown"
    ]
    stage: Literal[
        "upload", "parse", "chunk", "embed", "graph", "finalize",
        "archive", "delete", "purge", "unknown"
    ] = "unknown"
    progress_ratio: float | None = None
    message: str | None = None
    error_message: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None
    chunks_count: int | None = None
    assets_count: int | None = None
    lightrag: dict[str, Any] | None = None  # safe summary only
```

### DomainProcessingStatusResponse

```python
class DomainProcessingStatusResponse(BaseModel):
    domain_id: str
    domain_status: str
    pipeline_busy: bool = False
    destructive_busy: bool = False
    scanning: bool = False
    active_job_name: str | None = None
    latest_message: str | None = None
    history_tail: list[str] = []
    document_counts: dict[str, int] = {}
    active_documents: list[DocumentProcessingStatusResponse] = []
    failed_documents: list[DocumentProcessingStatusResponse] = []
    updated_at: datetime
    source: Literal["context_engine", "lightrag", "combined"]
    stale: bool = False
    poll_error: str | None = None
```

### ProcessingStatusListResponse

```python
class ProcessingStatusListResponse(BaseModel):
    domain_id: str
    documents: list[DocumentProcessingStatusResponse]
    jobs: list[JobStatusSummary]
    domain_status: DomainProcessingStatusResponse
    pagination: Pagination | None = None
    status_counts: dict[str, int] = {}
    updated_at: datetime
```

## Minimal routes

| Route | Auth | Purpose |
|---|---|---|
| `GET /documents/{document_id}/processing-status` | document readable user or admin | single document status, safe fields only |
| `GET /lightrag/domains/{domain_id}/processing-status` | authenticated user with domain visibility | user-safe domain indexing status |
| `GET /admin/lightrag/domains/{domain_id}/processing-status` | admin | detailed domain processing/runtime status |
| `GET /admin/lightrag/domains/{domain_id}/documents/processing-status` | admin | paginated document status list |
| `GET /admin/jobs` or existing jobs route | admin | queue/job status surface |

## Wiring rules

- Frontend API client: `client/src/api/processing-status.ts`.
- Do not place status fetching inside retrieve adapter.
- Do not place domain status polling inside `SidePanel` directly.
- Add one polling hook/store, for example `client/src/stores/processing-status-store.ts` or `client/src/hooks/use-domain-processing-status.ts`.
- Poll only when the relevant UI is visible.
- Use admin route only in admin settings.
- Use user-safe route in chat/workspace.

## Backend request coalescing/cache

Start simple:

- Cache per-domain status snapshot in process memory for 2–5 seconds while busy.
- Cache 15–30 seconds while idle.
- On LightRAG failure, return last known snapshot with `stale=true` and `poll_error`.
- If multiple requests arrive for same domain while a poll is in-flight, share the same task/result where practical.

Do not add Redis/pubsub/SSE until HTTP polling proves insufficient.
