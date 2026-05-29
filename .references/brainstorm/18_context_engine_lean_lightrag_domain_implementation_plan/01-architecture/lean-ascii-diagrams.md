# Lean ASCII Diagrams

## Product surface

```text
┌────────────────────────────────────────────────────────────────────────────┐
│                         ADMIN SETTINGS UI                                 │
│                                                                            │
│  AI Settings                           LightRAG Domains                    │
│  ───────────                           ────────────────                    │
│  Provider API keys                     Create                              │
│  Model profiles                        Start                               │
│  Default LLM profile                   Stop                                │
│  Default embedding profile             Delete                              │
└────────────────────────────────────────────────────────────────────────────┘
```

## Final lifecycle

```text
        ┌──────────────┐
        │   Create     │
        │ config only  │
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │  Stopped /   │
        │  Configured  │
        └──────┬───────┘
               │ Start
               ▼
        ┌──────────────┐
        │   Running    │
        └──────┬───────┘
               │ Stop
               ▼
        ┌──────────────┐
        │   Stopped    │
        └──────┬───────┘
               │ Delete
               ▼
        ┌──────────────┐
        │   Deleted    │
        │ safe archive │
        └──────────────┘
```

## Start as the only boot path

```text
Admin clicks Start
       │
       ▼
POST /admin/lightrag/domains/{id}/up
       │
       ▼
LightRAGDomainService.up()
       │
       ├── prepare runtime artifacts
       │     ├── ensure folders
       │     ├── ensure/provision Postgres
       │     ├── resolve runtime config
       │     ├── read current provider secrets
       │     ├── use domain embedding snapshot
       │     ├── write domain.env
       │     └── write generated Compose
       │
       ├── docker compose build/up
       │
       ├── health probe
       │
       └── persist status
```

## Provider setting change flow

```text
Admin changes provider key/model profile
       │
       ▼
/admin/ai-settings
       │
       ▼
Runtime DB
  ├── ai_model_profiles
  ├── ai_model_settings
  └── ai_provider_secrets
       │
       ▼
Running containers are unchanged
       │
       ▼
UI should show: restart required
       │
       ▼
Admin Stop/Start or Start if stopped
       │
       ▼
Start rewrites domain.env with current secrets/config
```

## Retrieval defaults policy

```text
Backend deployment settings
       │
       ▼
LightRAGDeploySettings / runtime config resolver
       │
       ▼
write_domain_env()
       │
       ▼
.data/lightrag/domains/<id>/domain.env
       │
       ▼
LightRAG container reads env at start
```

Retrieval defaults do not pass through the UI or create-domain API.
