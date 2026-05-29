# Executive Summary

## Decision

Simplify the LightRAG domain deployment control plane to:

```text
Create
Start
Stop
Delete
```

Remove these public operations:

```text
repair
recreate
regenerate
purge-preview
purge
```

Remove runtime retrieval defaults from the domain creation UI and API. Retrieval defaults should be deployment/runtime configuration written into `domain.env`, not values edited during domain creation or runtime.

## Why this is the right low-bloat target

The current system exposes too many technical operations as product actions. `repair`, `recreate`, and `regenerate` are implementation details around runtime artifact generation and Docker restart behavior. `purge` is a dangerous permanent-delete path that forces extra UI, API contracts, preview handling, tests, and edge cases.

The lean system keeps the real technical work but hides it behind a simpler product model.

```text
Start = prepare runtime artifacts + write domain.env + write Compose + provision Postgres + boot Docker + health check
```

## Product-facing controls after refactor

```text
LightRAG Domains:
  - Create domain
  - Start domain
  - Stop domain
  - Delete domain

AI Settings:
  - Provider API keys
  - Model profiles
  - Default LLM profile
  - Default embedding profile
```

## Not product-facing after refactor

```text
repair
recreate
regenerate
purge
purge-preview
retrieval defaults
advanced retrieval presets
Docker force-recreate
manual config regeneration
```

## Key implementation change

Create should not start the container.

```text
Current: Create -> may call repair -> starts/recreates container
Target:  Create -> writes config only
         Start  -> boots runtime
```

## Data retention decision

Delete should be safe delete/archive, not hard purge.

Delete should:

- remove the domain from active manifest;
- rewrite generated Compose without the service;
- move runtime domain files to a deleted/archive folder;
- preserve document rows, uploads, jobs, parsed structure, chunks, and assets.

Permanent hard cleanup can be implemented later as an offline operator script, not a normal web route.
