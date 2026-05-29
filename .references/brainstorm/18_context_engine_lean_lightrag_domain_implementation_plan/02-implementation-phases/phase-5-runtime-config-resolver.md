# Phase 5 — Runtime Config Resolver

## Goal

Reduce wiring spread by creating one internal service that resolves everything needed to write `domain.env` at Start time.

## New file suggestion

```text
app/services/lightrag_runtime_config_resolver.py
```

Or place under deploy if you prefer:

```text
app/lightrag_deploy/runtime_config.py
```

## Responsibilities

The resolver should produce one typed object containing:

```text
LLM runtime config
Embedding runtime config
Provider secret values
Postgres runtime config
Retrieval defaults from deploy settings
```

## What it should not do

It should not:

- write files;
- call Docker;
- mutate manifest;
- provision Postgres;
- expose secrets in API responses.

## Why this helps

Currently, provider/model/runtime/env wiring can be spread across AI settings service, model profile resolver, domain service, deploy settings, and compose writer.

The resolver gives Start a clean dependency:

```python
runtime_config = resolver.resolve_for_domain_start(domain)
write_domain_env(domain, paths, runtime_config)
```

## Acceptance criteria

- Start code is easier to read.
- Env writer receives a typed runtime config.
- Provider secret values only exist in memory and generated `domain.env`.
- Tests can fake runtime config resolver without needing full AI settings DB.
