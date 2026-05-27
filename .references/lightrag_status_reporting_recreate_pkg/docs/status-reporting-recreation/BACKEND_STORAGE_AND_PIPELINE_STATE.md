# Backend Storage and Pipeline State

## Durable Document Status

LightRAG stores per-document processing state in `doc_status` storage.

Implementations exist for multiple storage backends, including JSON, PostgreSQL, Redis, MongoDB, and others.

The key pattern is:

```text
doc_status row/document
  id
  content_summary
  content_length
  file_path
  status
  created_at
  updated_at
  track_id
  chunks_count
  chunks_list
  error_msg
  metadata
  content_hash
```

## Track ID

A `track_id` groups one upload/insert/scan request to the status rows it created.

LightRAG-style format:

```text
{prefix}_{YYYYMMDD_HHMMSS}_{8-char-uuid}
```

Examples:

```text
upload_20260526_143010_ab12cd34
insert_20260526_143011_6f9a2b10
scan_20260526_143020_9c8d7e6f
enqueue_20260526_143030_1a2b3c4d
```

Prefixes to preserve:

```text
upload
insert
scan
enqueue
```

## Live Pipeline Status

`pipeline_status` is a shared live state namespace.

Recommended fields:

```text
autoscanned
busy
destructive_busy
scanning
scanning_exclusive
pending_enqueues
job_name
job_start
docs
batchs
cur_batch
request_pending
cancellation_requested
latest_message
history_messages
```

## Why Track ID and Pipeline Status Are Both Needed

Do not collapse these concepts.

| Concept | Scope | Persistence | UI use |
|---|---|---|---|
| `track_id` | one upload/insert/scan batch | durable through doc_status | exact result of a user action |
| `pipeline_status` | global pipeline worker state | live/shared state | progress dialog and active indicator |

## Required State Transitions

```text
Accepted upload
  → doc_status pending

Worker starts document
  → doc_status processing
  → pipeline_status.busy true
  → pipeline_status.latest_message "Processing document..."

Parser/chunker completed
  → doc_status preprocessed or processing with chunks_count

Graph/vector indexing completed
  → doc_status processed

Exception
  → doc_status failed
  → error_msg set
  → pipeline_status.latest_message set

Pipeline complete
  → pipeline_status.busy false
  → latest_message "Document processing pipeline completed"
```

## Concurrency Flags to Copy

LightRAG’s newer pattern includes more than `busy`.

Recommended flags:

```text
busy
  true while pipeline processing or destructive jobs run

destructive_busy
  true while clear/delete operations can drop storage or remove files

scanning
  true during scan lifecycle

scanning_exclusive
  true only during scan classification phase

pending_enqueues
  number of accepted upload/insert requests whose background enqueue has not written doc_status yet

request_pending
  tells the processing loop to pick up new docs after current batch
```

## Practical Simpler Version

For a smaller codebase, start with:

```text
busy
pending_enqueues
request_pending
cancellation_requested
latest_message
history_messages
```

Add `destructive_busy` and `scanning_exclusive` if you support clear/delete/scan concurrently with upload.

## Storage Interface to Recreate

```python
class DocStatusRepository:
    async def create_pending(
        self,
        doc_id: str,
        file_path: str,
        content_summary: str,
        content_length: int,
        track_id: str,
        metadata: dict,
    ) -> None: ...

    async def update_status(
        self,
        doc_id: str,
        status: DocStatus,
        *,
        chunks_count: int | None = None,
        error_msg: str | None = None,
        metadata_patch: dict | None = None,
    ) -> None: ...

    async def get_docs_by_track_id(
        self,
        track_id: str,
    ) -> dict[str, DocProcessingStatus]: ...

    async def get_docs_paginated(
        self,
        status_filter: DocStatus | None,
        status_filters: list[DocStatus] | None,
        page: int,
        page_size: int,
        sort_field: str,
        sort_direction: str,
    ) -> tuple[list[tuple[str, DocProcessingStatus]], int]: ...

    async def get_all_status_counts(self) -> dict[str, int]: ...
```

## Pipeline State Interface to Recreate

```python
class PipelineStatusStore:
    async def get(self) -> PipelineStatus: ...
    async def update(self, patch: dict[str, Any]) -> None: ...
    async def append_message(self, message: str) -> None: ...
    async def acquire_enqueue_slot(self) -> None: ...
    async def release_enqueue_slot(self) -> None: ...
    async def acquire_destructive_busy(self) -> bool: ...
    async def request_cancel(self) -> None: ...
```

## Implementation Note for Multi-Process Servers

If the app runs with multiple worker processes, in-memory dicts are not enough. Use one of:

```text
Redis
database row/table
multiprocessing manager
file lock + JSON
```

For `context_engine`, Redis + PostgreSQL is likely cleaner:

```text
PostgreSQL → durable document/job statuses
Redis      → live pipeline progress and fast mutable state
```
