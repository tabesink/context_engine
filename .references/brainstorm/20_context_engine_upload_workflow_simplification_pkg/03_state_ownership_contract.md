# Upload State Ownership Contract

Commit this as:

```text
docs/architecture/upload_status_state_ownership.md
```

## Owner map

```text
documents.status
  Owns current document availability.

operations.status
  Owns active/recent work status.

operations.stage
  Owns current processing phase.

operations.message
  Owns short user-facing progress message.

operations.error_message
  Owns operation failure reason.

documents.error_message
  Owns current document-level failure reason.

documents.metadata.lightrag
  Owns remote identifiers/fingerprints/last-check data only.

processing-status endpoints
  Own UI read model composition.

worker
  Owns execution of ingest operation.

poller/reconciler
  Owns remote LightRAG reconciliation only.
```

## Do not use metadata as source of truth

Avoid:

```json
{
  "lightrag": {
    "status": "queued"
  }
}
```

Preferred:

```json
{
  "lightrag": {
    "domain_id": "fatigue",
    "embedding_profile_id": "openai-text-embedding-3-small",
    "embedding_fingerprint": "...",
    "remote_document_id": "...",
    "last_remote_check_at": "..."
  }
}
```

If remote status must be stored temporarily, name it clearly:

```json
{
  "lightrag": {
    "last_remote_status": "processing",
    "last_remote_check_at": "..."
  }
}
```

Never treat `last_remote_status` as the app source of truth.

## Allowed transitions

### Document

```text
uploaded -> indexing -> ready
uploaded -> indexing -> failed
failed   -> indexing -> ready
failed   -> indexing -> failed
any      -> deleted
```

### Operation

```text
queued -> running -> succeeded
queued -> running -> failed
queued -> canceled
running -> canceled
```

### Stage

```text
queued
saving
parsing
extracting_assets
indexing_lightrag
waiting_remote
complete
failed
```

Keep stage scalar and simple. Do not create a separate event table yet.
