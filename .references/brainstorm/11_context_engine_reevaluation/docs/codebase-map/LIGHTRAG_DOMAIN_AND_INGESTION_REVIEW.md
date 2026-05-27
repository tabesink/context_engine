# LightRAG Domain and Ingestion Review

## Desired Flow

```text
Admin selects Provider/default embedding profile
  → creates LightRAG domain
  → domain stores embedding snapshot
  → admin uploads document to domain
  → worker parses document
  → local pages/sections/chunks/assets are stored
  → chunks are ingested into selected LightRAG domain
  → domain and document become available for retrieval
```

## Current Positive Findings

The modified codebase appears to include:

- LightRAG admin routes
- LightRAG domain create request with `embedding_profile_id`
- domain embedding snapshot
- provider/model resolver
- domain env generation
- admin upload route with optional domain parameter
- domain validation before upload
- background ingestion job
- parsed local structure persistence
- remote LightRAG chunk ingestion

## Important Architecture Issue

The domain model is currently stronger for **embedding profile snapshots** than for full Provider profile control.

That may be acceptable if documented:

```text
Embedding profile is domain-level and locked.
LLM profile is global/default and may change over time.
```

But the Settings UI says Provider, so the product behavior must be explicit.

## Recommended Domain Rules

### Rule 1: Domain Must Lock Embedding Profile

A domain should store:

```text
embedding_profile_id
embedding_provider
embedding_binding
embedding_base_url
embedding_model
embedding_dimensions
embedding_token_limit
embedding_fingerprint
embedding_locked_at
```

### Rule 2: Existing Domains Cannot Silently Switch Embedding Model

Allowed options:

```text
Option A: never allow embedding model change after domain creation.
Option B: allow change only before first document ingestion.
Option C: allow change only through explicit full reindex workflow.
```

Recommended low-entropy choice:

```text
Option B now.
Option C later.
```

### Rule 3: Upload Must Persist Domain and Embedding Identity

Document should store:

```text
lightrag_domain_id
embedding_profile_id or embedding_fingerprint
ingestion_status
```

Store it both as first-class DB fields and in metadata if needed for backward compatibility.

## Current Risk: Secret Resolution During Domain Env Generation

The domain env generation path must be able to resolve secrets saved through the admin Provider settings UI.

If the domain service only sees OS environment variables, then UI-saved API keys will not work.

Required fix:

```text
LightRAGDomainService
  → ModelProfileResolver
  → AIModelSettingsService
  → AIProviderSecretRepository
  → SecretCryptoService
```

## Upload/Ingestion Acceptance Criteria

- Admin upload requires valid target domain.
- Upload fails clearly if domain does not exist.
- Upload fails clearly if domain is not ready/configured.
- Upload persists document with domain ID.
- Worker stores local parsed structure.
- Worker sends chunks to correct LightRAG domain.
- Worker updates job status on success/failure.
- Ingestion records embedding fingerprint used.
- Mismatched embedding profile is rejected.
