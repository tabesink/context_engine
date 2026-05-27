# Provider Settings Review

## Desired Product Behavior

The Settings sub-route currently framed as `LLM Model` / `ai-models` should become `Provider`.

This is not just a label change. The provider page should own:

- provider type
- base URL
- API key / credential state
- allowed LLM models
- default LLM model
- allowed embedding models
- default embedding model
- embedding dimension / token limit, where needed
- provider connection test
- admin-only update behavior

## Current Evidence-Based Finding

Backend provider configuration appears to exist primarily through environment settings and LightRAG generated domain env files.

Observed backend settings include LightRAG LLM and embedding values such as:

```text
LIGHTRAG_LLM_BINDING
LIGHTRAG_LLM_BINDING_HOST
LIGHTRAG_LLM_BINDING_API_KEY
LIGHTRAG_LLM_MODEL
LIGHTRAG_EMBEDDING_BINDING
LIGHTRAG_EMBEDDING_BINDING_HOST
LIGHTRAG_EMBEDDING_BINDING_API_KEY
LIGHTRAG_EMBEDDING_MODEL
LIGHTRAG_EMBEDDING_DIM
```

The generated domain env writer appends these provider values into LightRAG domain environment files.

However, no backend provider router was observed in the registered app routes, and no provider profile table was observed in the inspected storage schema.

## Required Backend Shape

Recommended minimal backend model:

```text
ProviderProfile
  id
  name
  provider_type
  base_url
  api_key_secret_ref or encrypted_api_key
  default_llm_model
  allowed_llm_models
  default_embedding_model
  allowed_embedding_models
  embedding_dim
  embedding_token_limit
  is_active
  created_by
  created_at
  updated_at
```

## Recommended API

Admin-only:

```text
GET    /admin/providers
POST   /admin/providers
GET    /admin/providers/{provider_id}
PATCH  /admin/providers/{provider_id}
POST   /admin/providers/{provider_id}/test
DELETE /admin/providers/{provider_id}
```

User-safe or optional:

```text
GET /providers/public
```

This endpoint must not expose secrets. It can return names, provider type, enabled status, default model labels, and masked API key status.

## Supported Provider Types

Recommended enum:

```text
openai
bedrock_openai_compatible
ollama_openai_compatible
```

## Provider Compatibility Notes

| Provider | Internal Shape | Notes |
|---|---|---|
| OpenAI | OpenAI-compatible base URL + API key + model names | Straightforward |
| Bedrock OpenAI-compatible | OpenAI-compatible base URL + bearer/API key style credential | Keep as base URL + secret; do not hardcode OpenAI-only assumptions |
| Ollama OpenAI-compatible | local base URL, often no real API key | Allow empty/fake key depending adapter/client needs |

## Required UI Changes

Change frontend settings route union from something like:

```text
"general" | "account" | "knowledge-graph" | "ai-models"
```

to something like:

```text
"general" | "account" | "knowledge-graph" | "provider"
```

Add a Provider page with:

- provider selector
- base URL input
- API key input with masked saved state
- LLM model dropdown/input
- embedding model dropdown/input
- embedding dimension field
- test connection button
- admin-only guard

## Acceptance Criteria

- Settings sidebar shows `Provider`, not `LLM Model` or `AI Models`.
- Only admins can view/edit provider secrets.
- Backend rejects provider writes for regular users.
- API key is never returned unmasked.
- Provider test endpoint returns status without leaking credentials.
- Provider config can be used by LightRAG domain creation/env generation.
