# 01 — Architecture Decision

## Decision

Use Amazon Bedrock's OpenAI-compatible API endpoint through LightRAG's existing OpenAI-compatible configuration surface:

```env
LLM_BINDING=openai
LLM_BINDING_HOST=https://bedrock-runtime.<region>.amazonaws.com/openai/v1
LLM_BINDING_API_KEY=<Amazon Bedrock API key>
LLM_MODEL=<Bedrock OpenAI-compatible model id>

EMBEDDING_BINDING=openai
EMBEDDING_BINDING_HOST=<embedding endpoint>
EMBEDDING_BINDING_API_KEY=<embedding key>
EMBEDDING_MODEL=<embedding model>
EMBEDDING_DIM=<dimension>
```

## Why this is the right fit for the current codebase

The current app already has these layers:

```text
Context Engine
  ├── FastAPI app
  ├── document metadata / structure / assets
  ├── local navigation retrieval
  ├── LightRAG domain deployment generation
  └── LightRAG HTTP adapter

LightRAG domain service
  ├── semantic indexing
  ├── graph/vector storage
  ├── LLM calls for extraction/querying
  └── embedding calls
```

The model-provider API key belongs in the **LightRAG domain service**, not in the `context_engine` request path.

Therefore the implementation should extend the LightRAG deployment generator so the generated per-domain `domain.env` includes provider settings from root `.env`.

## Why not native Bedrock binding right now?

Native Bedrock binding is a valid future option, but the user selected **Option B: Bedrock OpenAI-compatible endpoint**. That means the implementation should minimize code changes by using LightRAG's existing `openai` binding and only changing the base URL/key/model values.

## Runtime diagram

```text
User / TUI / Frontend
        │
        ▼
Context Engine API
        │
        │ uses LIGHTRAG_BASE_URL + LIGHTRAG_API_KEY
        ▼
LightRAG domain container
        │
        │ uses LLM_BINDING=openai
        │ uses LLM_BINDING_HOST=https://bedrock-runtime.<region>.amazonaws.com/openai/v1
        │ uses LLM_BINDING_API_KEY=<Bedrock API key>
        ▼
Amazon Bedrock OpenAI-compatible endpoint
```

## Important distinction

| Variable | Owner | Purpose |
|---|---|---|
| `LIGHTRAG_API_KEY` | Context Engine + LightRAG server | Authenticates Context Engine calls into LightRAG. |
| `LIGHTRAG_LLM_BINDING_API_KEY` | LightRAG domain env | Authenticates LightRAG calls into Bedrock/OpenAI-compatible endpoint. |
| `LIGHTRAG_EMBEDDING_BINDING_API_KEY` | LightRAG domain env | Authenticates LightRAG embedding calls. |

## Current gap in the repo

Current files already support LightRAG deployment and per-domain env generation, but only storage/runtime values are written into `domain.env`.

Files to modify:

```text
app/core/config.py
app/lightrag_deploy/settings.py
app/lightrag_deploy/compose.py
.env.example
tests/test_lightrag_deploy_settings.py
tests/test_lightrag_deploy_manifest_compose.py
```

## Security rule

Provider keys must never be stored in:

```text
.data/lightrag/domains.json
API responses
logs
audit logs
query logs
```

They may appear only in:

```text
root .env
per-domain generated domain.env
Docker/Compose process environment
```

