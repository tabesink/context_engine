# API Contracts

## Upload

```http
POST /documents/upload
Content-Type: multipart/form-data
```

Response:

```json
{
  "status": "success",
  "message": "File 'example.pdf' uploaded successfully. Processing will continue in background.",
  "track_id": "upload_20260526_143010_ab12cd34"
}
```

## Track Status

```http
GET /documents/track_status/{track_id}
```

Response:

```json
{
  "track_id": "upload_20260526_143010_ab12cd34",
  "documents": [
    {
      "id": "doc-abc",
      "content_summary": "example.pdf",
      "content_length": 12345,
      "status": "processing",
      "created_at": "2026-05-26T14:30:10Z",
      "updated_at": "2026-05-26T14:30:40Z",
      "track_id": "upload_20260526_143010_ab12cd34",
      "chunks_count": 12,
      "error_msg": null,
      "metadata": {},
      "file_path": "example.pdf"
    }
  ],
  "total_count": 1,
  "status_summary": {
    "processing": 1
  }
}
```

## Pipeline Status

```http
GET /documents/pipeline_status
```

Response:

```json
{
  "autoscanned": false,
  "busy": true,
  "job_name": "indexing files",
  "job_start": "2026-05-26T14:30:11Z",
  "docs": 4,
  "batchs": 2,
  "cur_batch": 1,
  "request_pending": false,
  "cancellation_requested": false,
  "latest_message": "Processing batch 1 of 2",
  "history_messages": [
    "Starting document processing pipeline",
    "Processing batch 1 of 2"
  ],
  "update_status": {}
}
```

## Paginated Documents

```http
POST /documents/paginated
Content-Type: application/json
```

Request:

```json
{
  "status_filter": null,
  "status_filters": ["preprocessed", "processing"],
  "page": 1,
  "page_size": 50,
  "sort_field": "updated_at",
  "sort_direction": "desc"
}
```

Response:

```json
{
  "documents": [],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_count": 0,
    "total_pages": 0,
    "has_next": false,
    "has_prev": false
  },
  "status_counts": {
    "all": 0,
    "pending": 0,
    "processing": 0,
    "preprocessed": 0,
    "processed": 0,
    "failed": 0
  }
}
```

## Status Counts

```http
GET /documents/status_counts
```

Response:

```json
{
  "status_counts": {
    "all": 10,
    "pending": 1,
    "processing": 2,
    "preprocessed": 1,
    "processed": 5,
    "failed": 1
  }
}
```

## Health

```http
GET /health
```

Status-related fields:

```json
{
  "status": "healthy",
  "pipeline_busy": true,
  "pipeline_active": true,
  "pipeline_scanning": false,
  "pipeline_destructive_busy": false,
  "pipeline_pending_enqueues": 0
}
```

## Cancel Pipeline

```http
POST /documents/cancel_pipeline
```

Response:

```json
{
  "status": "cancellation_requested",
  "message": "Pipeline cancellation has been requested. Documents will be marked as FAILED."
}
```
