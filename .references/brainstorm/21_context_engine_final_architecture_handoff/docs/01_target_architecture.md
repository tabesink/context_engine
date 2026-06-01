# 01 — Target Architecture

## Final Architecture Principle

```text
Documents own uploaded files and local structure.
Domains own LightRAG runtime/workspace identity.
Operations own all async/global visibility.
processing-status is the only document status API.
Provider config is static/env-driven unless intentionally retained as runtime-admin editable.
Frontend talks to one typed API layer.
```

## Target System Diagram

```text
┌─────────────────────────────────────────────────────────────────┐
│ Next.js Frontend                                                 │
├─────────────────────────────────────────────────────────────────┤
│ app routes                                                       │
│ components                                                       │
│ stores                                                           │
│ typed API clients: auth/documents/domains/operations/provider    │
└───────────────────────────────┬─────────────────────────────────┘
                                │ JSON + Bearer token
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ FastAPI Backend                                                  │
├─────────────────────────────────────────────────────────────────┤
│ routes                                                           │
│  ├─ auth                                                         │
│  ├─ documents/admin-documents                                    │
│  ├─ retrieve                                                     │
│  ├─ domains                                                      │
│  ├─ operations                                                   │
│  ├─ provider                                                     │
│  └─ users                                                        │
│                                                                 │
│ services                                                         │
│  ├─ DocumentService                                              │
│  ├─ DocumentProcessingService                                    │
│  ├─ LightRAGIngestionService                                     │
│  ├─ RetrievalService                                             │
│  ├─ DomainService                                                │
│  ├─ OperationService                                             │
│  ├─ ProviderConfigService                                        │
│  └─ AuditService                                                 │
└───────────────┬──────────────────┬──────────────────┬──────────┘
                │                  │                  │
                ▼                  ▼                  ▼
        ┌──────────────┐   ┌──────────────┐   ┌─────────────────┐
        │ PostgreSQL   │   │ Redis/RQ     │   │ LightRAG domain │
        │ app metadata │   │ operations   │   │ containers      │
        └──────────────┘   └──────────────┘   └─────────────────┘
```

## Ownership Boundaries

### Documents

Documents own:

```text
original uploaded file metadata
owner/domain relationship
processing status
local parsed structure
pages/sections/blocks
assets/images/tables
source chunks/citation mapping
```

Documents do **not** own:

```text
Docker lifecycle
provider defaults
global operation history
```

### Domains

Domains own:

```text
LightRAG workspace identity
host/port/container metadata
desired lifecycle state
embedding model identity at creation time
observed health status
```

Domains do **not** own:

```text
document upload buttons in a More menu
document viewer routing
duplicated logs/status pages when operations already exists
```

### Operations

Operations own:

```text
async/global activity visibility
status/stage/progress/error
who triggered the action
what resource was affected
```

Operations should cover:

```text
document ingestion
document retry/reingest
domain create/start/stop/delete
long-running provider tests, if applicable
```

### Provider Config

For the lean target:

```text
.env / domain.env = source of truth
Provider UI = display + diagnostics
Embedding model fixed per domain
Retrieval defaults are not runtime-editable
```

## Recommended Backend Route Shape

```text
/auth
/documents
/admin/documents
/retrieve
/domains
/admin/domains
/operations
/admin/provider
/users
```

## Recommended Frontend Route Shape

```text
/login
/chat
/documents
/documents/[id]
/settings/account
/settings/provider
/settings/domains
/settings/users
/operations
```

## Key Architecture Decision

Do not try to simplify by deleting everything at once. Simplify by making ownership explicit first, then migrate callers to canonical contracts, then deprecate unused paths.
