# Retrieval Defaults Policy

## Decision

Retrieval defaults are no longer product/runtime-editable settings.

Remove these from domain creation UI/API:

```text
top_k
chunk_top_k
chunk_rerank_top_k
max_token_for_text_unit
max_token_for_global_context
max_token_for_local_context
retrieval profile presets
```

## Why

These are not identity-level domain fields. They are runtime tuning defaults for LightRAG. Exposing them during domain creation makes the UI harder to understand and creates more API/schema/manifest surface to maintain.

## Final ownership

```text
Backend deployment settings
  -> LightRAGDeploySettings
  -> write_domain_env()
  -> domain.env
  -> LightRAG runtime
```

## Recommended env setting names

Add or keep deployment-level settings such as:

```text
LIGHTRAG_DEFAULT_TOP_K
LIGHTRAG_DEFAULT_CHUNK_TOP_K
LIGHTRAG_DEFAULT_CHUNK_RERANK_TOP_K
LIGHTRAG_DEFAULT_MAX_TOKEN_FOR_TEXT_UNIT
LIGHTRAG_DEFAULT_MAX_TOKEN_FOR_GLOBAL_CONTEXT
LIGHTRAG_DEFAULT_MAX_TOKEN_FOR_LOCAL_CONTEXT
```

Then write to `domain.env` as:

```text
TOP_K=...
CHUNK_TOP_K=...
CHUNK_RERANK_TOP_K=...
MAX_TOKEN_FOR_TEXT_UNIT=...
MAX_TOKEN_FOR_GLOBAL_CONTEXT=...
MAX_TOKEN_FOR_LOCAL_CONTEXT=...
```

Use the exact env names expected by the current LightRAG container wrapper. Verify actual names in `compose.py` before editing.

## Manifest policy

Preferred: remove `retrieval_defaults` from domain manifest.

The manifest should track domain identity, embedding snapshot, runtime URLs, paths, and status. It should not become a dumping ground for runtime tuning knobs.

## Compatibility option

If removing the manifest field is too large for one PR:

1. Stop accepting retrieval defaults from the frontend/API.
2. Keep writing default values to manifest for one compatibility window.
3. Stop reading manifest retrieval defaults when writing `domain.env`.
4. Remove manifest field in a later cleanup.
