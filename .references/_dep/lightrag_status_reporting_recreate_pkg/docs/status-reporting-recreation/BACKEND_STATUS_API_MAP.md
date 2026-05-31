# Backend Status API Map

## API Endpoints to Recreate

| Endpoint | Purpose | UI consumer |
|---|---|---|
| `POST /documents/upload` | Accept file, return immediate `track_id` | Upload dialog |
| `GET /documents/track_status/{track_id}` | Show per-upload status for all docs in that upload batch | Upload batch tracker / toast / detail view |
| `GET /documents/pipeline_status` | Show global pipeline job progress and messages | Pipeline status dialog |
| `POST /documents/cancel_pipeline` | Request cancellation of active pipeline | Pipeline status dialog cancel button |
| `POST /documents/paginated` | Fetch document table rows and status counts | Document manager table |
| `GET /documents/status_counts` | Fetch aggregate counts by status | Filter badges / dashboard |
| `GET /health` | Fetch high-level backend status, including `pipeline_active` | Global health store / polling cadence |

## Endpoint Responsibilities

### `POST /documents/upload`

Responsibilities:

```text
validate file
sanitize filename
reject conflicting filename/status when appropriate
write file to input/upload directory
generate track_id
reserve enqueue slot
schedule background task
return InsertResponse(status, message, track_id)
```

Do **not** wait for ingestion to complete.

### `GET /documents/track_status/{track_id}`

Responsibilities:

```text
query doc_status storage for all docs with track_id
map each record to DocStatusResponse
return TrackStatusResponse:
  track_id
  documents[]
  total_count
  status_summary
```

This endpoint answers: “What happened to the work initiated by my upload?”

### `GET /documents/pipeline_status`

Responsibilities:

```text
read shared pipeline_status namespace
copy mutable state to normal dict
truncate history_messages to safe max length
format job_start timestamp
include update_status flags if available
return PipelineStatusResponse
```

This endpoint answers: “What is the pipeline doing right now?”

### `POST /documents/paginated`

Responsibilities:

```text
query doc_status rows with page, page_size, sort field, sort direction
query status counts in parallel
return documents + pagination + status_counts
```

This endpoint powers the main document table and status filter counts.

### `GET /health`

Responsibilities:

```text
return backend health/configuration
include pipeline_busy
include pipeline_active
include pipeline_scanning
include pipeline_destructive_busy
include pipeline_pending_enqueues
```

This endpoint is used by the WebUI to keep global health and polling cadence synchronized.

## Recommended Status API Contract for Reimplementation

```python
class InsertResponse(BaseModel):
    status: Literal["success", "partial_success", "failure"]
    message: str
    track_id: str

class DocStatusResponse(BaseModel):
    id: str
    content_summary: str
    content_length: int
    status: Literal[
        "pending",
        "processing",
        "preprocessed",
        "processed",
        "failed",
    ]
    created_at: str
    updated_at: str
    track_id: str | None = None
    chunks_count: int | None = None
    error_msg: str | None = None
    metadata: dict[str, Any] | None = None
    file_path: str

class TrackStatusResponse(BaseModel):
    track_id: str
    documents: list[DocStatusResponse]
    total_count: int
    status_summary: dict[str, int]

class PipelineStatusResponse(BaseModel):
    autoscanned: bool = False
    busy: bool = False
    job_name: str = "-"
    job_start: str | None = None
    docs: int = 0
    batchs: int = 0
    cur_batch: int = 0
    request_pending: bool = False
    cancellation_requested: bool | None = None
    latest_message: str = ""
    history_messages: list[str] | None = None
    update_status: dict[str, Any] | None = None
```

## Status Values

Recommended canonical values:

```text
pending       accepted, not yet processed
processing    actively being parsed/chunked/indexed
preprocessed  parsed/chunked but waiting for final graph/vector processing
processed     fully usable for retrieval
failed        terminal failure, error_msg explains why
```

If your backend has more granular states, group them for the UI:

```text
parsing/analyzing/preprocessed → analyzing
processing                     → processing
pending                        → pending
processed                      → processed
failed                         → failed
```
