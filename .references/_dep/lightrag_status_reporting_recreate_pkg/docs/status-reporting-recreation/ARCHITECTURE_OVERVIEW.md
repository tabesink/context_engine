# Architecture Overview

## What LightRAG Status Reporting Solves

LightRAG needs to give users immediate feedback after upload while ingestion continues in the background.

The status design separates two user questions:

1. **What happened to my upload?**
   - Answered by `track_id` and `/documents/track_status/{track_id}`.

2. **What is the global ingestion/indexing pipeline doing right now?**
   - Answered by `/documents/pipeline_status` and `/health`.

## High-Level Flow

```text
User uploads document
  → POST /documents/upload
  → backend saves file
  → backend generates track_id
  → backend starts background pipeline_index_file(...)
  → client receives success + track_id immediately
  → background task extracts content
  → LightRAG apipeline_enqueue_documents(..., track_id)
  → doc_status writes PENDING records
  → apipeline_process_enqueue_documents()
  → pipeline_status updates busy/job/progress/messages
  → per-document doc_status updates:
        PENDING
        PROCESSING
        PREPROCESSED
        PROCESSED
        FAILED
  → WebUI polls APIs and renders:
        document table status
        status filter counts
        pipeline active indicator
        pipeline status dialog
        upload progress
        error/details dialog
```

## Two Status Mechanisms

### 1. Per-upload tracking

```text
track_id
  → ties one upload/insert/scan batch to one or more doc_status rows
  → used for exact upload result tracking
```

### 2. Global pipeline status

```text
pipeline_status namespace
  → busy
  → scanning
  → destructive_busy
  → pending_enqueues
  → job_name
  → docs
  → batchs
  → cur_batch
  → latest_message
  → history_messages
  → cancellation_requested
```

## Why This Design Works

The design separates durable state from live operational state:

```text
doc_status
  → durable per-document processing state
  → survives process restart depending storage backend

pipeline_status
  → live operational state
  → tells the UI what the current pipeline is doing
```

That separation is the most important pattern to copy.

## Recreate in Your Codebase

Use the same conceptual boundaries:

```text
Upload route
  → returns job_id/track_id immediately

Job/document status table
  → durable per-document state

Pipeline state store
  → global active job progress

Background worker
  → owns transitions and messages

Frontend API client
  → polls status endpoints

Frontend components
  → document table, progress dialog, upload status, status filters
```
