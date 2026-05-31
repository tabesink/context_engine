# Documents Surface Status Rules

## The Documents surface owns

```text
Upload document
List documents
Show processing state
Retry failed document ingestion
Open ready documents
```

## Status chip labels

```text
uploaded -> Uploaded
queued   -> Queued
indexing -> Processing
ready    -> Ready
failed   -> Failed
deleted  -> Deleted
```

## Action visibility

```text
Upload button:
  visible to admin users

Retry button:
  visible when can_retry=true

Open/View button:
  visible when status=ready

Delete button:
  visible to admin users if supported
```

## Do not show

```text
Raw job IDs as primary text
Raw LightRAG pipeline status as primary status chip
Manual refresh button in normal row actions
Worker/poller implementation details
```
