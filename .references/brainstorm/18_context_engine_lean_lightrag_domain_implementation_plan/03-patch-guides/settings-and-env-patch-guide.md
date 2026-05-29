# Settings and Env Patch Guide

## Goal

Make retrieval defaults backend/deployment config only.

## Add or verify config settings

In `app/core/config.py` or equivalent settings model, define defaults such as:

```python
lightrag_default_top_k: int = 10
lightrag_default_chunk_top_k: int = 10
lightrag_default_chunk_rerank_top_k: int = 10
lightrag_default_max_token_for_text_unit: int = 4000
lightrag_default_max_token_for_global_context: int = 4000
lightrag_default_max_token_for_local_context: int = 4000
```

Map from env vars:

```text
LIGHTRAG_DEFAULT_TOP_K
LIGHTRAG_DEFAULT_CHUNK_TOP_K
LIGHTRAG_DEFAULT_CHUNK_RERANK_TOP_K
LIGHTRAG_DEFAULT_MAX_TOKEN_FOR_TEXT_UNIT
LIGHTRAG_DEFAULT_MAX_TOKEN_FOR_GLOBAL_CONTEXT
LIGHTRAG_DEFAULT_MAX_TOKEN_FOR_LOCAL_CONTEXT
```

## Update deploy settings

Add to `LightRAGDeploySettings` or its equivalent so env writing does not need to inspect domain manifest defaults.

## Update `write_domain_env()`

Before:

```text
read domain.retrieval_defaults
```

After:

```text
read settings/runtime_config.retrieval_defaults
```

## Update `.env.example`

Add the new backend/deployment env vars with comments.

## Remove from create schema

Remove retrieval defaults from the create request.

## Remove from frontend create type

Remove from `CreateKnowledgeGraphDomainPayload`.

## Tests

Add tests that generated `domain.env` contains defaults from settings.
