# ADRs to Write

## ADR-001: Track ID vs Job ID

Decision:

- Whether the system uses LightRAG-style `track_id`, existing job IDs, or both.

Recommended:

```text
Use track_id for user-facing upload/insert/scan batches.
Use internal job IDs for queue/worker implementation if needed.
```

## ADR-002: Durable Document Status Storage

Decision:

- Where per-document status lives.

Recommended:

```text
Store per-document ingestion status in PostgreSQL.
Use Redis only for live mutable pipeline progress.
```

## ADR-003: Global Pipeline Status Store

Decision:

- Where live pipeline state lives.

Recommended:

```text
Use Redis key per workspace/domain for live pipeline status.
```

## ADR-004: Polling Strategy

Decision:

- How often the frontend polls.

Recommended:

```text
Document list: 5s active, 30s idle.
Pipeline dialog: 2s only while open.
Track status: optional 2s until terminal.
Health: existing app cadence.
```

## ADR-005: Cancellation Semantics

Decision:

- What cancellation does to already-processing documents.

Recommended:

```text
Cancellation sets a flag. Worker checks between major processing units.
Unprocessed docs become failed/cancelled with clear error_msg.
```

## ADR-006: Multi-Workspace / Multi-Domain Status

Decision:

- Whether status is global or per domain/workspace.

Recommended for context_engine:

```text
Pipeline status should be domain-scoped:
pipeline_status:{lightrag_domain_id}
```

## ADR-007: Upload Conflicts and Duplicate Handling

Decision:

- Whether same-name files are rejected or versioned.

Recommended:

```text
Reject same-name conflicts with HTTP 409 unless versioning is explicitly supported.
```
