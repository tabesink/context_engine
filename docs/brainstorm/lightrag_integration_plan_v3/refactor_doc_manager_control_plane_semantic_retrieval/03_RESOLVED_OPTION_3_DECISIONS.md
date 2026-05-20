# Resolved Option 3 Decisions

This document is the implementation handoff for combining the LightRAG-only semantic retrieval refactor with Option 3 shared PostgreSQL infrastructure.

## Storage Ownership

Option 3 means shared infrastructure, not shared data ownership.

- Context Engine PostgreSQL stores document/control metadata only.
- LightRAG owns semantic chunks, embeddings, vector indexes, graph storage, and document status internals.
- LightRAG persistent storage uses PostgreSQL for all supported layers: `PGKVStorage`, `PGDocStatusStorage`, `PGGraphStorage`, and `PGVectorStorage`.
- Redis is reserved for Context Engine jobs, locks, cache, and coordination.

## Domain Isolation

Each LightRAG domain gets its own PostgreSQL database and LightRAG workspace.

Example:

```text
Domain ID: manuals
PostgreSQL database: lightrag_manuals
LightRAG WORKSPACE: manuals
Redis lock key: lightrag:domain:manuals:ingest_lock
```

The domain manifest may record non-secret database metadata such as the database name, but it must not contain passwords.

## Provisioning

Context Engine's LightRAG domain manager provisions domain storage when a domain is created.

- Root `.env` contains the admin provisioning DSN.
- Context Engine creates the domain database and limited runtime credential.
- The generated `domain.env` contains LightRAG runtime credentials.
- `domains.json` contains only non-secret manifest data.
- Normal remove archives domain files and leaves destructive cleanup explicit.
- Permanent delete may drop the domain database only when permanent deletion is enabled.

## Docker Topology

Root services and generated LightRAG domain services use a shared named Docker network.

LightRAG containers connect to PostgreSQL by service name:

```text
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
```

Host-published ports are for local developer access only.

## PostgreSQL Image Requirement

The selected LightRAG storage combination requires:

- `vector` for `PGVectorStorage`;
- Apache `AGE` for `PGGraphStorage`.

The Postgres service must use a validated image or local build that supports both extensions. Option 3 is not ready until a smoke test can create both extensions in a throwaway database.

## LightRAG Runtime Image

LightRAG domain containers are built from the local `external/lightrag` package using a Context Engine-owned Dockerfile. The checked-in package currently reports LightRAG version `1.4.16`.

## Upload And Status

Upload is a control-plane action.

- Upload accepts `semantic_engine="lightrag"`.
- Any other semantic engine is rejected.
- Upload stores the raw file and local document metadata.
- Upload enqueues a `lightrag_ingest_document` job.
- The ingestion job serializes same-domain ingestion with a Redis lock.
- The ingestion job uploads to LightRAG and polls status until ready, failed, or timeout.
- A manual refresh endpoint remains available for recovery.

## Navigation

Navigation is separate from semantic retrieval.

- `documents.status` remains the query-facing semantic readiness state.
- `documents.metadata.lightrag` records LightRAG domain, remote IDs, track ID, status, message, and last check time.
- `documents.metadata.navigation` records whether local page/tree navigation is enabled and ready.
- Navigation processing never marks semantic retrieval ready or failed.

## Retrieval Modes

- `semantic`: LightRAG only.
- `navigation`: local parsed pages/navigation only.
- `hybrid`: LightRAG semantic evidence plus local navigation enrichment when available.

No retrieval mode may read `semantic_chunks`.

## API Contract Notes

Context Engine uses `X-API-Key` for LightRAG API-key auth, matching `external/lightrag`.
