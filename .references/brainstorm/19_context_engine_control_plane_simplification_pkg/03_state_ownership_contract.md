# State Ownership Contract

This document should be committed into the repo under:

```text
docs/architecture/control_plane_state_ownership.md
```

## Core rule

Never let the same state be independently owned by more than one table.

## Document state

Owner:

```text
documents.status
```

Purpose:

```text
Current document availability for list screens and query eligibility.
```

Allowed values:

```text
uploaded
indexing
ready
failed
deleted
```

Not responsible for:

```text
Detailed task progress
Worker heartbeat
Domain container state
Historical event log
```

## Domain state

Owner:

```text
lightrag_domains.state
```

Purpose:

```text
Current LightRAG domain availability and lifecycle status.
```

Recommended lean values:

```text
creating
stopped
starting
running
stopping
failed
deleted
```

Do not expose repair/recreate/regenerate/purge as normal UI lifecycle states.

## Operation state

Owner:

```text
operations.status
```

or during compatibility phase:

```text
jobs.status + new operation fields
```

Purpose:

```text
Source of truth for active/recent long-running work.
```

Allowed values:

```text
queued
running
succeeded
failed
canceled
```

Resource typing:

```text
document
  document ingestion, parse, index, reindex

domain
  create, start, stop, delete

provider
  model test, provider health check, secret validation

system
  maintenance, one-off admin operation
```

## Audit state

Owner:

```text
audit_logs
```

Purpose:

```text
Append-only history of important admin/security/system actions.
```

Rules:

- Do not update audit rows after creation.
- Do not use audit logs as the current state source.
- Actor can be nullable for system actions.

## Query telemetry

Owner:

```text
query_logs
```

Purpose:

```text
Retrieval analytics: query text, mode, latency, evidence count, user, created_at.
```

Rules:

- Keep separate from audit logs unless product decides query analytics are unnecessary.
- Do not store full evidence payloads by default.

## Metadata fields

JSON `metadata` fields are allowed for flexible context, but they must not become hidden state machines.

Bad:

```json
{
  "status": "running",
  "domain_state": "active",
  "job_status": "failed"
}
```

Good:

```json
{
  "compose_project": "ce-fatigue",
  "container_name": "ce-fatigue-lightrag",
  "last_probe_ms": 42
}
```
