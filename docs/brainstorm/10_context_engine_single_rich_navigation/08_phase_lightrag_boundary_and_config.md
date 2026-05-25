# 08 — Phase: LightRAG Boundary and Config Cleanup

## Goal

Prevent Context Engine from becoming a second LightRAG deployment/config system unless that is explicitly desired.

## Architectural Boundary

```text
Context Engine:
  users
  documents
  rich local navigation
  retrieval orchestration
  admin/TUI/API

LightRAG:
  embeddings
  semantic retrieval
  graph retrieval
  vector/graph storage
```

## Decide Control-Plane Scope

## Option A — Leanest

Context Engine does not manage LightRAG containers.

It only:

```text
reads configured domains
calls LightRAG APIs
shows status
```

Remove:

```text
Docker lifecycle mutation APIs
compose generation
domain up/down/recreate/remove API routes
most lightrag_deploy code
```

## Option B — Acceptable

Keep deployment as script/ops tooling only.

```text
scripts/deploy-lightrag.sh
.data/lightrag/domains.json
```

Remove Docker lifecycle mutation from the app API.

## Config Cleanup Rule

```text
Context Engine .env configures Context Engine.
LightRAG .env configures LightRAG.
```

## Context Engine Should Keep

```text
APP_NAME
ENVIRONMENT
SECRET_KEY
ACCESS_TOKEN_MINUTES
DATABASE_URL
REDIS_URL
STORAGE_ROOT
ALLOWED_ORIGINS

LIGHTRAG_ENABLED=true
LIGHTRAG_BASE_URL
LIGHTRAG_API_KEY
LIGHTRAG_DOMAIN
LIGHTRAG_DOMAINS_MANIFEST
LIGHTRAG_TIMEOUT_SECONDS
```

## Move Out or Remove

```text
LightRAG image/build config
LightRAG internal Postgres config
LightRAG internal Redis config
LightRAG Neo4j config
LightRAG model/env deployment values
Docker compose binary/execution config
Port allocation logic
archive/delete lifecycle policy
```

## Graph Route Cleanup

Make graph routes domain-scoped:

```text
GET /lightrag/domains/{domain_id}/graphs
GET /lightrag/domains/{domain_id}/graph/labels
GET /lightrag/domains/{domain_id}/graph/labels/popular
GET /lightrag/domains/{domain_id}/graph/labels/search
```

Or remove graph routes until graph UX is required.

## Acceptance Criteria

```text
[ ] Clear decision: external LightRAG only or script-managed LightRAG.
[ ] App config no longer duplicates LightRAG deployment config.
[ ] Domain selection is explicit and consistent.
```
