# 1. Final Architecture Decisions

## 1.1 Final Product Shape

`context_engine` is the single operator-facing application.

Operators should not need to run Easy Deploy LightRAG directly. Instead, Context Engine should expose the useful Easy Deploy capabilities through its own backend API and terminal UI.

`easy-deploy-lightrag` is source material only:

- reuse concepts
- reuse simple algorithms where appropriate
- do not copy its whole app structure
- do not introduce a second CLI, backend, or frontend
- do not vendor LightRAG internals into `app/`

## 1.2 Core Principle

```text
Merge capabilities, not internal complexity.
```

That means Context Engine should gain the capability to create/manage LightRAG domains, but it should not absorb the entire Easy Deploy app or LightRAG internals.

## 1.3 Data Plane vs Control Plane

This split is the key to avoiding redundancy.

### Data Plane: runtime LightRAG use

The existing HTTP-only LightRAG adapter remains the runtime boundary.

```text
User query / upload / graph request
  ↓
Context Engine API
  ↓
RetrievalService / DocumentService / Graph route
  ↓
LightRAGRemoteAdapter
  ↓
HTTP request to selected running LightRAG domain
```

Data-plane responsibilities:

- query/retrieve/answer through LightRAG
- upload forwarding to LightRAG
- status polling from LightRAG
- graph proxy requests
- normalize LightRAG evidence into Context Engine response contracts

### Control Plane: domain deployment and lifecycle

The new module handles deployment/admin operations only.

```text
Admin TUI / Admin API
  ↓
Context Engine LightRAG domain service
  ↓
manifest + generated env + generated compose
  ↓
Docker Compose
  ↓
running LightRAG domain container
```

Control-plane responsibilities:

- create domain
- validate domain ID and port
- create `.data/lightrag/domains/<domain>/...`
- generate domain env files
- update manifest
- generate compose file
- start/stop/recreate containers
- archive/remove domains
- health/status checks

## 1.4 What Must Not Happen

Avoid these entropy traps:

```text
BAD:
- TUI screen calls Docker directly
- TUI screen calls LightRAG directly
- CLI/TUI duplicates backend business logic
- Retrieval adapter starts/stops containers
- Deployment module performs retrieval
- Context Engine imports LightRAG internals
- Easy Deploy repo is copied wholesale
- Root `.env.example` and domain env files become competing sources of truth
- Multiple domain registries exist
- Normal users can mutate domains or indexes
```

## 1.5 Final Architecture

```text
                         ┌──────────────────────────────┐
                         │  Context Engine Terminal UI  │
                         │  cli/launcher.py + cli/tui   │
                         └───────────────┬──────────────┘
                                         │
                                         ▼
                                cli/services/*
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Context Engine API                          │
│                                                                     │
│  Existing runtime routes                                             │
│   ├── /query, /query/retrieve, /query/answer                         │
│   ├── /admin/documents/upload                                        │
│   ├── /graphs, /graph/label/...                                      │
│   └── /lightrag/domains or similar read list for normal users         │
│                                                                     │
│  New admin control routes                                            │
│   └── /admin/lightrag/domains/...                                    │
│                                                                     │
└───────────────┬───────────────────────────────────────┬─────────────┘
                │                                       │
                ▼                                       ▼
     Existing runtime adapter                 New deployment manager
 app/integrations/lightrag_remote_adapter     app/lightrag_deploy/*
                │                                       │
                ▼                                       ▼
     Running LightRAG domain HTTP API          .data + generated compose
```

## 1.6 Final Module Placement

Add a new small module:

```text
app/lightrag_deploy/
  __init__.py
  models.py
  settings.py
  paths.py
  manifest.py
  compose.py
  docker_runner.py
  health.py
  service.py
  errors.py
```

Keep existing runtime integration in:

```text
app/integrations/lightrag_remote_adapter.py
app/integrations/lightrag_domains.py
app/retrieval/lightrag_remote_engine.py
app/api/routes/lightrag.py
```

## 1.7 Why This Is Simple

The system has only one owner for each responsibility:

| Responsibility | Owner |
|---|---|
| Auth/RBAC | Existing Context Engine auth/deps |
| Document registry | Existing Context Engine document model/repository |
| Query/retrieve/answer | Existing Context Engine query/retrieval services |
| Runtime LightRAG HTTP calls | Existing `LightRAGRemoteAdapter` |
| Domain deployment lifecycle | New `app/lightrag_deploy/service.py` |
| TUI presentation | `cli/tui/` screens |
| TUI API calls | `cli/services/` |
| Configuration source of truth | Root `.env.example` + `app/core/config.py` |
| Runtime generated files | `.data/lightrag/...` |
