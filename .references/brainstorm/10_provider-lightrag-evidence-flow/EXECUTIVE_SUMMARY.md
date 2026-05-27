# Executive Summary

## Readiness Judgment

The modified `context_engine` repo is close to having the right backend foundation, but it is not yet ready for the full provider → LightRAG ingestion → user chat evidence → workspace tree/context panel flow.

The backend already has the right direction:

```text
FastAPI
  → admin/auth/document/retrieve/LightRAG/workspace-tree routes
  → DocumentService / RetrievalService / LightRAG services
  → PostgreSQL + Redis/RQ
  → LightRAG as remote semantic retrieval service
  → local document navigation and asset storage
```

The frontend also has relevant pieces:

```text
Next.js client
  → chat shell
  → retrieval settings
  → workspace tree component
  → side/context panel component
  → settings users route
```

However, the provider-centered configuration model is still mostly missing as a product feature.

## Top 5 Blockers

### 1. Provider settings are environment-oriented, not admin-configurable

Provider values exist in backend settings and generated LightRAG domain env files, but no provider profile route/service/table was found.

### 2. Settings route needs product rename and deeper behavior change

Frontend settings has `ai-models` as a route concept. The target should be `provider`, because the admin is configuring provider profile, credentials, LLM model, embedding model, base URL, and connection status.

### 3. LightRAG domains do not store embedding model identity or lock state

Domain creation models store domain identity, ports, service names, URLs, paths, status, and health. They do not appear to store provider profile ID, embedding model, embedding dimension, or embedding lock metadata.

### 4. Frontend chat contract does not match backend `/retrieve`

Backend `/retrieve` returns structured `RetrieveResponse` evidence/assets. Frontend chat types use streaming events, LightRAG-ish query modes, and context panel item shapes. A mapping layer or route alignment is required.

### 5. Workspace tree and context panel are not fully contract-aligned

Backend workspace-tree endpoint exists, and backend evidence has useful top-level fields. Frontend tree/context-panel components exist, but they appear to be populated from chat stream state rather than the backend workspace-tree + retrieve evidence contract.

## Preserve These Strong Choices

- Keep `/retrieve` as the canonical backend evidence API.
- Keep admin-only write boundaries.
- Keep LightRAG as a remote service boundary.
- Keep local Context Engine document structure and assets separate from LightRAG internals.
- Keep regular-user retrieval and workspace-tree read access.
- Keep embedding model consistency as a domain-level invariant.

## Recommended Target Shape

```text
Admin Settings / Provider page
  → ProviderProfile admin API
  → ProviderProfileService
  → ProviderProfileRepository / secret handling
  → LightRAGDomainService uses provider profile snapshot
  → LightRAG domain stores provider + embedding identity
  → DocumentService validates domain before upload
  → Worker ingests local structure and LightRAG chunks
  → RetrievalService retrieves and enriches evidence
  → Frontend maps RetrieveResponse to context panel + workspace tree
```
