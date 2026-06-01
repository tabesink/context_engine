# 09 — Junior Developer Checklist

Use this checklist while implementing the final architecture refactor.

## Before You Edit

- [ ] Confirm you are on a new branch from `v1`.
- [ ] Read `README.md`.
- [ ] Read `app/main.py`.
- [ ] Read the relevant route file before editing a service.
- [ ] Read the relevant service before editing a repository/model.
- [ ] Search frontend usages before changing an endpoint.

## Safe Rule

Never remove a backend endpoint until the frontend no longer calls it and tests prove the replacement works.

## Key Concepts

### Document

An uploaded file and its local parsed structure.

Owns:

```text
filename
owner
storage path
status
pages
sections
blocks
assets
source chunks
LightRAG domain id
```

### Domain

A LightRAG workspace/runtime.

Owns:

```text
domain id
display name
host port
container name
desired state
observed health
embedding model
```

### Operation

A visible async task.

Owns:

```text
type
status
stage
progress
resource
actor
error
created/updated timestamps
```

### Provider Config

The LLM/embedding configuration source.

Lean target:

```text
env/domain.env owns it
UI displays diagnostics
runtime defaults are not casually editable
```

## Implementation Safety Checklist

### Status Refactor

- [ ] Replace frontend `ingestion-status` with `processing-status`.
- [ ] Keep deprecated backend wrappers temporarily.
- [ ] Add comments explaining deprecation.
- [ ] Add tests.

### Operations Refactor

- [ ] Do not rename the `jobs` table unless explicitly planned.
- [ ] Make `/operations` the frontend contract.
- [ ] Keep `/jobs` debug/deprecated only.
- [ ] Verify operations show document ingest and domain lifecycle actions.

### Domain UI Refactor

- [ ] Domain menu only has Start, Stop, Delete.
- [ ] Upload document is not in domain More menu.
- [ ] View documents is not in domain More menu.
- [ ] View logs is not in domain More menu unless there is a dedicated logs route.

### Provider Refactor

- [ ] Do not expose secret values.
- [ ] Do not allow changing embedding model for existing domain unless explicitly supported.
- [ ] Do not leave runtime retrieval defaults editable if env owns defaults.

### Frontend API Refactor

- [ ] Move endpoint strings into `client/src/lib/api`.
- [ ] Keep components mostly presentational.
- [ ] Keep stores focused on state, not random API calls.

## Files to Read First

```text
app/main.py
app/api/routes/documents.py
app/api/routes/admin.py
app/api/routes/retrieve.py
app/api/routes/jobs.py
app/api/routes/operations.py
app/api/routes/lightrag_domains.py
app/api/routes/lightrag_admin.py
app/api/routes/ai_settings.py
app/services/document_service.py
app/services/job_service.py
app/services/lightrag_ingestion_service.py
app/services/retrieval_service.py
app/storage/models.py
client/src/lib/api/*
client/src/stores/auth-store.ts
client/src/stores/lightrag-domain-store.ts
```

## Red Flags

Stop and ask for review if you see:

```text
A route duplicated under two names
A UI component hardcoding backend URLs
A migration dropping a table immediately
Provider secrets being returned to frontend
Domain lifecycle code writing state in more than one place
A worker creating duplicate operations while polling
```
