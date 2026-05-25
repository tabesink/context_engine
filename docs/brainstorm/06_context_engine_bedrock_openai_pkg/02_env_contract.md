# 02 — Environment Contract

## Add these variables to root `.env.example`

Add a new section after the existing LightRAG deployment/storage settings.

```env
# ---------------------------------------------------------------------
# LightRAG model provider configuration
# ---------------------------------------------------------------------
# These values are written into each generated LightRAG domain.env.
# They configure how LightRAG calls the LLM and embedding provider.
#
# For Amazon Bedrock OpenAI-compatible Chat Completions, keep the binding
# as `openai` and point the host at the Bedrock OpenAI-compatible endpoint:
#   https://bedrock-runtime.<region>.amazonaws.com/openai/v1
#
# Important:
# - LIGHTRAG_API_KEY authenticates Context Engine -> LightRAG.
# - LIGHTRAG_LLM_BINDING_API_KEY authenticates LightRAG -> provider.
# - For Bedrock OpenAI-compatible API, this must be a Bedrock API key,
#   not an OpenAI API key.

LIGHTRAG_LLM_BINDING=openai
LIGHTRAG_LLM_BINDING_HOST=https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1
LIGHTRAG_LLM_BINDING_API_KEY=
LIGHTRAG_LLM_MODEL=openai.gpt-oss-20b-1:0

# Optional role-specific overrides. Leave blank to let LightRAG fall back
# to the global LLM settings.
LIGHTRAG_KEYWORD_LLM_MODEL=
LIGHTRAG_QUERY_LLM_MODEL=
LIGHTRAG_VLM_LLM_MODEL=

# Embeddings. Do not change embedding model/dim after documents have been indexed
# unless you plan to rebuild the LightRAG domain index.
LIGHTRAG_EMBEDDING_BINDING=openai
LIGHTRAG_EMBEDDING_BINDING_HOST=https://api.openai.com/v1
LIGHTRAG_EMBEDDING_BINDING_API_KEY=
LIGHTRAG_EMBEDDING_MODEL=text-embedding-3-large
LIGHTRAG_EMBEDDING_DIM=3072
LIGHTRAG_EMBEDDING_TOKEN_LIMIT=8192
LIGHTRAG_EMBEDDING_SEND_DIM=false
LIGHTRAG_EMBEDDING_USE_BASE64=true

# Optional OpenAI-compatible tuning. Keep blank unless needed.
LIGHTRAG_OPENAI_LLM_MAX_TOKENS=9000
LIGHTRAG_OPENAI_LLM_MAX_COMPLETION_TOKENS=
LIGHTRAG_OPENAI_LLM_TEMPERATURE=
LIGHTRAG_OPENAI_LLM_EXTRA_BODY=
```

## Recommended `.env` for Bedrock OpenAI-compatible LLM + OpenAI embeddings

This is the most practical first version because Bedrock OpenAI-compatible support for chat/generation is clear, while embeddings may vary by provider/model/region.

```env
LIGHTRAG_ENABLED=true
LIGHTRAG_DEPLOY_ENABLED=true

# Context Engine -> LightRAG server auth
LIGHTRAG_API_KEY=change-this-server-api-key

# LightRAG -> Amazon Bedrock OpenAI-compatible Chat Completions
LIGHTRAG_LLM_BINDING=openai
LIGHTRAG_LLM_BINDING_HOST=https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1
LIGHTRAG_LLM_BINDING_API_KEY=your-bedrock-api-key
LIGHTRAG_LLM_MODEL=openai.gpt-oss-20b-1:0

# LightRAG -> OpenAI embeddings
LIGHTRAG_EMBEDDING_BINDING=openai
LIGHTRAG_EMBEDDING_BINDING_HOST=https://api.openai.com/v1
LIGHTRAG_EMBEDDING_BINDING_API_KEY=your-openai-api-key
LIGHTRAG_EMBEDDING_MODEL=text-embedding-3-large
LIGHTRAG_EMBEDDING_DIM=3072
LIGHTRAG_EMBEDDING_TOKEN_LIMIT=8192
LIGHTRAG_EMBEDDING_SEND_DIM=false
LIGHTRAG_EMBEDDING_USE_BASE64=true
```

## Alternative `.env` if Bedrock/OpenAI-compatible embeddings are available

Use only after validating that the selected Bedrock endpoint/model supports the embedding call shape expected by LightRAG's OpenAI embedding client.

```env
LIGHTRAG_EMBEDDING_BINDING=openai
LIGHTRAG_EMBEDDING_BINDING_HOST=https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1
LIGHTRAG_EMBEDDING_BINDING_API_KEY=your-bedrock-api-key
LIGHTRAG_EMBEDDING_MODEL=<bedrock-openai-compatible-embedding-model-id>
LIGHTRAG_EMBEDDING_DIM=<actual-dimension>
```

## Generated `domain.env` should contain

After implementation, every generated domain env should include:

```env
LLM_BINDING=openai
LLM_BINDING_HOST=https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1
LLM_BINDING_API_KEY=your-bedrock-api-key
LLM_MODEL=openai.gpt-oss-20b-1:0

EMBEDDING_BINDING=openai
EMBEDDING_BINDING_HOST=https://api.openai.com/v1
EMBEDDING_BINDING_API_KEY=your-openai-api-key
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIM=3072
EMBEDDING_TOKEN_LIMIT=8192
EMBEDDING_SEND_DIM=false
EMBEDDING_USE_BASE64=true
```

## Generated `domain.env` should not contain

Do not put these into `domain.env` as model-provider keys:

```env
OPENAI_API_KEY=
OPENAI_BASE_URL=
```

Reason: LightRAG's config contract is `LLM_BINDING_*` and `EMBEDDING_BINDING_*`. Keeping the LightRAG-native names is clearer and avoids accidental conflicts with other libraries.

