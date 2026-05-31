# Polling Rules

## Document row polling

```text
Poll every 2 seconds while:
  operation_status = queued | running
  OR document.status = uploaded | indexing

Stop polling when:
  document.status = ready | failed | deleted
```

## Domain board polling

```text
Poll every 3 seconds while:
  domain.is_busy = true

Poll on refresh or every 15-30 seconds while idle.
```

## Error behavior

```text
If processing-status returns stale diagnostic:
  show local document status
  show subtle helper text: "Remote status is temporarily unavailable. Showing latest local status."

Do not flip ready/failed back to processing based only on stale remote response.
```
