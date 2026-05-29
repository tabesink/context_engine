# Phase 4 — Retrieval Defaults Removal

## Goal

Move retrieval defaults out of runtime/domain UI/API and into backend deployment configuration written to `domain.env`.

## Remove from frontend

Remove fields/state/types for:

```text
top_k
chunk_top_k
chunk_rerank_top_k
max_token_for_text_unit
max_token_for_global_context
max_token_for_local_context
retrieval profile presets
```

## Remove from backend create request

Remove from `LightRAGDomainCreateRequest`.

## Remove from domain manifest, preferred

Preferred final state: domain manifest does not store retrieval defaults.

If too risky, use two-step compatibility:

1. Stop accepting retrieval defaults from UI/API.
2. Continue writing default values to manifest if old code expects them.
3. Stop reading manifest retrieval defaults when writing `domain.env`.
4. Remove field later.

## Add backend settings

Add or verify settings in `app/core/config.py` and/or `LightRAGDeploySettings`:

```text
LIGHTRAG_DEFAULT_TOP_K
LIGHTRAG_DEFAULT_CHUNK_TOP_K
LIGHTRAG_DEFAULT_CHUNK_RERANK_TOP_K
LIGHTRAG_DEFAULT_MAX_TOKEN_FOR_TEXT_UNIT
LIGHTRAG_DEFAULT_MAX_TOKEN_FOR_GLOBAL_CONTEXT
LIGHTRAG_DEFAULT_MAX_TOKEN_FOR_LOCAL_CONTEXT
```

Use the exact variable names expected by LightRAG's runtime wrapper when writing `domain.env`.

## Update env writer

`write_domain_env()` should receive retrieval defaults from runtime/deploy settings, not from `domain.retrieval_defaults`.

## Acceptance criteria

- Create UI has no retrieval tuning.
- Create API has no retrieval tuning.
- Domain manifest does not depend on retrieval tuning fields.
- `domain.env` still includes retrieval defaults from backend config.
- Tests verify env output contains configured defaults.
