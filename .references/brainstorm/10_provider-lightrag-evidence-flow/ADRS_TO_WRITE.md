# ADRs to Write

## ADR-001: Provider Profile Model

Decision: provider profiles are first-class admin-managed objects or env-managed profiles with optional DB-backed extension.

Must answer:

- where provider config lives
- how provider types are represented
- whether profiles are domain-scoped or global
- how default provider is selected

## ADR-002: Secret Handling

Decision: API keys are env-managed, encrypted in DB, or external secret refs.

Must answer:

- how raw keys are stored
- how keys are masked
- who can write keys
- whether logs can include provider config

## ADR-003: LightRAG Domain Embedding Lock

Decision: domains cannot silently change embedding model after ingestion.

Recommended:

```text
Embedding config can change only while domain is empty.
After first successful ingestion, domain is locked.
Change requires explicit rebuild/reindex.
```

## ADR-004: Canonical Retrieval API

Decision: `/retrieve` is canonical for evidence retrieval.

Must answer:

- whether streaming chat wraps RetrievalService
- whether any duplicate query endpoints remain
- stable evidence response shape

## ADR-005: Evidence and Context Panel Contract

Decision: define stable fields between backend and frontend.

Must include:

- reference_id
- document_id
- document_title
- source_path
- chunk_id
- page information
- assets

## ADR-006: Shared Corpus Read Model

Decision: all authenticated users can read ready shared-domain documents; only admins write.

Must be explicit if no tenant/private document isolation exists.

## ADR-007: LightRAG Boundary

Decision: Context Engine owns auth, metadata, structured navigation, API contract, and orchestration; LightRAG owns semantic/vector/graph retrieval internals.
