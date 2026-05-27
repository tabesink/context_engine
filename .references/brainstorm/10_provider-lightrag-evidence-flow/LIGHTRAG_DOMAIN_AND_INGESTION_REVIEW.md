# LightRAG Domain and Ingestion Review

## Current Domain Model Gap

The inspected LightRAG domain model includes domain identity, display name, workspace, Postgres names, host/port, service/container names, URLs, paths, status, default flag, health, and timestamps.

It does not appear to include:

```text
provider_profile_id
provider_type
llm_model
embedding_model
embedding_dim
embedding_model_locked_at
embedding_fingerprint
```

## Why This Matters

Embedding model consistency is a hard invariant.

A LightRAG domain with existing indexed documents must not silently switch embedding model, because vectors produced by different embedding models or dimensions should not be mixed in the same index.

## Recommended Rule

Use this low-entropy rule:

```text
A LightRAG domain can choose/change embedding model only while empty.
After first successful ingestion, the embedding model is locked.
Changing embedding model requires explicit full rebuild/reindex workflow.
```

## Recommended Domain Fields

Add or equivalent:

```text
provider_profile_id
llm_model
embedding_model
embedding_dim
embedding_token_limit
embedding_locked_at
embedding_lock_reason
first_ingested_document_id
```

## Domain Creation Flow

Target:

```text
Admin creates domain
  → selects provider profile
  → selects embedding model from allowed list
  → selects optional default LLM model
  → domain stores provider/profile/model snapshot
  → generated LightRAG env uses domain-specific config
  → domain starts with stable provider settings
```

## Domain Update Flow

Allowed:

- display name change
- default flag change
- LLM model change, if runtime supports it
- provider profile change only if embedding model/dim stay compatible or domain is empty

Blocked:

- embedding model change after ingestion
- embedding dimension change after ingestion
- provider change that implies a different embedding model/dimension after ingestion

## Current Ingestion Flow Strengths

The ingestion service already performs the right broad responsibilities:

```text
fetch document
  → resolve LightRAG domain
  → acquire domain lock
  → parse document
  → save local structure/artifacts
  → send source chunks to LightRAG adapter for that domain
```

## Required Ingestion Additions

Before enqueue or before ingestion starts:

```text
validate domain exists
validate domain status is ingest-ready
validate provider profile is configured
validate embedding config is set
validate document.embedding_model matches domain.embedding_model
lock embedding model on first successful ingestion
```

## Partial Failure Behavior

Required status handling:

```text
local parse failed
  → document ingestion_status = failed_parse
  → no LightRAG ingestion attempted

local parse succeeded, LightRAG ingest failed
  → document lightrag_status = failed
  → local structure retained
  → retry supported

LightRAG ingested, local update failed
  → mark inconsistent / needs reconciliation
  → admin-visible remediation
```

## Tests Required

- domain creation requires provider profile
- domain stores embedding model/dim
- first ingestion locks embedding model
- upload fails if domain provider misconfigured
- upload fails if domain not ready
- upload cannot proceed without domain
- ingestion sends chunks to selected domain
- reingestion preserves domain embedding invariant
