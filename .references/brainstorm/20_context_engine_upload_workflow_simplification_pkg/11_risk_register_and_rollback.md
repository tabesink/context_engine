# Risk Register and Rollback

## Risk 1 — Breaking existing job workers

Cause:

```text
Renaming jobs to operations too early.
```

Mitigation:

```text
Add operation-compatible fields to jobs first.
Keep old fields and endpoints.
Introduce operation vocabulary at service/API layer gradually.
```

Rollback:

```text
Leave new columns unused. Revert service changes.
```

## Risk 2 — UI loses status updates

Cause:

```text
Switching from ingestion-status/jobs to processing-status before response includes all needed fields.
```

Mitigation:

```text
Add missing fields to processing-status first.
Run UI smoke test.
Only then remove old polling usage.
```

Rollback:

```text
Restore old polling usage temporarily.
```

## Risk 3 — Metadata status still treated as authoritative

Cause:

```text
Old code reads metadata.lightrag.status and overrides operation/document state.
```

Mitigation:

```text
Search all metadata.lightrag.status reads/writes.
Replace with local operation/document status except raw diagnostic display.
```

Rollback:

```text
Keep metadata writes during transition but lower precedence in status composer.
```

## Risk 4 — Duplicate retry paths confuse users

Cause:

```text
UI exposes both job retry and document reingest/retry.
```

Mitigation:

```text
Normal UI exposes document retry only.
Jobs retry remains admin diagnostics only.
```

Rollback:

```text
Keep job retry endpoint but hide it from Documents page.
```

## Risk 5 — Poller overwrites worker state incorrectly

Cause:

```text
Poller and worker both update statuses directly.
```

Mitigation:

```text
Both use DocumentIngestionStatusService.
Poller only updates waiting_remote/indexing documents.
```

Rollback:

```text
Disable poller temporarily; manual refresh remains emergency path.
```
