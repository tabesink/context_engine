# Architecture Decision Records to Write

## ADR-001: Shared Corpus Access Model

### Decision Needed

Is the current V1 product intentionally a shared knowledge base where all authenticated users can read all READY documents in visible domains?

### Recommended Decision

Yes, for V1.

```text
All authenticated users can read READY documents in visible shared domains.
Only admins can upload, reingest, delete/archive, or manage LightRAG domains.
No per-user private corpus exists in V1.
```

### Why

This matches the small-team internal deployment model and keeps the system simple.

### Consequences

- Easier frontend integration.
- Easier retrieval logic.
- Must not market this as tenant-isolated.
- Future private scopes require schema and policy changes.

---

## ADR-002: LightRAG Runtime Boundary

### Decision Needed

Should `context_engine` embed LightRAG internals or keep LightRAG as a remote service?

### Recommended Decision

Keep LightRAG as a remote HTTP service.

### Why

This preserves a clean adapter boundary and avoids duplicating LightRAG internals.

### Consequences

- Backend depends on LightRAG API stability.
- Need domain health/status monitoring.
- Need pinned LightRAG versions in production.

---

## ADR-003: Canonical Retrieval API

### Decision Needed

Should the app expose multiple query endpoints or a single retrieval endpoint?

### Recommended Decision

Use `/retrieve` as the canonical retrieval/evidence API.

### Why

Reduces frontend confusion and backend duplication.

### Consequences

- All retrieval modes must fit under one request/response contract.
- Evidence shape must be stable.
- Old query endpoints should be removed or deprecated.

---

## ADR-004: Document Archive and Hard Delete Policy

### Decision Needed

What happens to uploaded files, extracted assets, local rows, and LightRAG indexed data when a document/domain is archived or deleted?

### Recommended Decision

Separate archive from hard delete.

```text
Archive:
  - hide from active retrieval
  - retain files/assets/metadata
  - allow recovery

Hard delete:
  - admin-only destructive operation
  - remove files/assets/local rows
  - remove or rebuild LightRAG index
  - write audit record
```

---

## ADR-005: LightRAG Domain Registry Source of Truth

### Decision Needed

Is the source of truth a manifest file, database table, or hybrid?

### Recommended Decision

Use one primary source of truth and document reconciliation behavior.

### Why

Manifest/DB drift can break domain listing, retrieval, and deployment lifecycle.

---

## ADR-006: Provider Configuration Strategy

### Decision Needed

How should OpenAI, OpenAI-compatible Bedrock, and future providers be configured?

### Recommended Decision

Use provider profiles.

Example:

```text
PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_BASE_URL=...

PROVIDER=bedrock_openai_compatible
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://...
```

### Consequences

- Less scattered provider logic.
- Easier domain env generation.
- Cleaner docs for junior developers.

---

## ADR-007: CLI/TUI Support Status

### Decision Needed

Is CLI/TUI supported, deprecated, or developer-only?

### Recommended Decision

Retain as developer-only backend API harness if it remains useful.

### Consequences

- README and AGENTS.md must agree.
- CLI tests should be kept only if harness is supported.
- Product frontend should not depend on TUI behavior.

---

## ADR-008: Observability Strategy

### Decision Needed

Should observability be native only, external tool-based, or hybrid?

### Recommended Decision

Start with native structured logs and query/job/domain health metadata. Consider Langfuse or similar only for LLM/retrieval traces, cost, and evaluation once the app has active usage.

### Consequences

- Avoids overbuilding observability too early.
- Leaves a clean path for Langfuse later.
