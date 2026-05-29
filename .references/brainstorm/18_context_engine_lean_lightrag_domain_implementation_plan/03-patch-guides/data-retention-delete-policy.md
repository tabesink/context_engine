# Data Retention Delete Policy

## Decision

Delete is safe remove/archive, not permanent purge.

## Delete should remove active runtime

```text
remove domain from active manifest
rewrite Compose without service
move runtime folder to deleted/archive root
block future upload/retrieval/status for that domain
```

## Delete should preserve local records

```text
documents
jobs
uploaded originals
document pages
sections
blocks
source chunks
assets
audit logs
```

## Why

This avoids dangerous accidental deletion and keeps the app simple. Permanent cleanup can be handled later with an offline maintenance script if storage growth becomes a real problem.

## Required tests

- Delete removes domain from active list.
- Delete preserves document row count.
- Delete preserves document processing row count.
- Deleted domain cannot be selected for upload.
- Deleted domain cannot be queried.
