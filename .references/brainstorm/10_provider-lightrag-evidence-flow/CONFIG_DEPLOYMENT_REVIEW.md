# Configuration and Deployment Review

## Current Strengths

- `.env.lightrag-provider.example` documents provider values for generated LightRAG domain env files.
- Backend settings include LightRAG LLM and embedding configuration fields.
- Domain env generation appends provider env values into LightRAG domain env files.
- Docker Compose includes API, worker, status-poller, Redis, Postgres, and migration service.

## Required Provider Config Direction

Provider config should become a first-class domain/admin concept, not only global environment values.

Recommended layering:

```text
Environment variables
  → seed/default provider profile
  → admin Provider UI can show env-managed profile safely
  → domain creation chooses provider profile
  → domain env generation uses chosen provider profile snapshot
```

## Environment Variables to Keep

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

But these should represent a default provider profile, not the only configurable source.

## Provider Examples

### OpenAI

```text
provider_type=openai
base_url=https://api.openai.com/v1
api_key=sk-...
llm_model=gpt-4o-mini
embedding_model=text-embedding-3-large
embedding_dim=3072
```

### Bedrock OpenAI-Compatible

```text
provider_type=bedrock_openai_compatible
base_url=https://bedrock-runtime.../openai/v1
api_key=<bearer/API credential appropriate to deployment>
llm_model=<bedrock-openai-compatible-model>
embedding_model=<compatible embedding model, if supported>
```

### Ollama OpenAI-Compatible

```text
provider_type=ollama_openai_compatible
base_url=http://localhost:11434/v1
api_key=ollama or empty/fake if client requires one
llm_model=llama3.1 or selected local model
embedding_model=nomic-embed-text or selected local embedding model
```

## Deployment Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Provider values only global env | Cannot have per-domain embedding discipline | Add provider profile + domain snapshot |
| LightRAG image `latest` | Runtime drift | Pin image for staging/production |
| API key stored plain in DB | Secret leak risk | Encrypt or env-manage |
| Domain env not regenerated after provider change | Runtime mismatch | Restart/recreate domain explicitly |
| Ollama local URL inside container wrong | Connection failure | Document host networking / service name |
| Bedrock credential shape misunderstood | Auth failure | Keep generic OpenAI-compatible base URL + secret; test connection |

## Required Docs Updates

- `.env.example`
- `.env.lightrag-provider.example`
- Settings Provider admin guide
- LightRAG domain provider/embedding lock guide
- local Ollama setup guide
- Bedrock OpenAI-compatible setup guide
- production secret handling note
