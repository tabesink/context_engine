# Feature Spec: Admin AI Model Settings

## Goal

Add an admin-only settings section where admins can select:

1. default LLM provider/model
2. default embedding provider/model
3. allowed embedding models for new knowledge graph domains

These selections should become the default source of truth for other parts of the app that need a model, especially LightRAG domain creation.

## Why This Matters

Embeddings are not interchangeable across models. If one domain indexes documents with `text-embedding-3-large` and later queries or inserts documents with `bge-m3`, vector similarity quality becomes unreliable because the vectors live in different embedding spaces.

Therefore:

```text
A LightRAG domain must have exactly one embedding profile.
That embedding profile is selected at domain creation.
It cannot be changed after documents are indexed.
```

LLMs are different. LLMs affect text generation, extraction quality, and graph-building style, but they do not define the vector space. For V1, LLM defaults can be changed globally and used for future domain.env regeneration.

## Provider Scope for V1

### LLM providers

Enable only:

- OpenAI
- AWS Bedrock OpenAI-compatible endpoint
- local Ollama service

### Embedding providers

Enable only:

- OpenAI
- local Ollama service

Do **not** expose AWS Bedrock embedding models through the settings UI in V1 unless the team explicitly decides to support native Bedrock embeddings separately. AWS Bedrock OpenAI-compatible docs currently focus on OpenAI-style Chat Completions and Responses APIs. Native Bedrock embedding models such as Titan can be added later through a separate provider adapter.

## Default Seed Profiles

Recommended seed LLM profiles:

| Profile ID | Provider | Base URL | Model | Notes |
|---|---|---|---|---|
| `openai-gpt-4o-mini` | `openai` | `https://api.openai.com/v1` | `gpt-4o-mini` | Hosted default |
| `bedrock-gpt-oss-120b` | `bedrock_openai` | `https://bedrock-mantle.<region>.api.aws/v1` | `openai.gpt-oss-120b` | Region-specific |
| `ollama-qwen3-8b` | `ollama` | `http://host.docker.internal:11434/v1` | `qwen3:8b` | Local dev |

Recommended seed embedding profiles:

| Profile ID | Provider | Base URL | Model | Dimensions | Token Limit | Notes |
|---|---|---|---|---:|---:|---|
| `openai-text-embedding-3-small` | `openai` | `https://api.openai.com/v1` | `text-embedding-3-small` | 1536 | 8192 | Cheaper hosted default |
| `openai-text-embedding-3-large` | `openai` | `https://api.openai.com/v1` | `text-embedding-3-large` | 3072 | 8192 | Higher quality |
| `ollama-nomic-embed-text` | `ollama` | `http://host.docker.internal:11434/v1` | `nomic-embed-text` | configured | configured | Local default |
| `ollama-bge-m3` | `ollama` | `http://host.docker.internal:11434/v1` | `bge-m3` | configured | 8192 | Strong multilingual option |

Use `host.docker.internal` for container-to-host Ollama access in local Docker environments. For Linux deployments, document the Docker network alternative if `host.docker.internal` is unavailable.

## Product Rules

### Rule 1: Admin-only access

Only admins can:

- view AI model settings
- create/edit/disable model profiles
- set default LLM profile
- set default embedding profile
- select embedding profile when creating a new LightRAG domain

Regular users should not see this settings route.

### Rule 2: Secrets are not edited in the UI for V1

The UI should show:

```text
OPENAI_API_KEY: present / missing
AWS_BEARER_TOKEN_BEDROCK: present / missing
Ollama: no key required
```

Do not store raw API keys in the browser or return them from the API.

### Rule 3: Embedding profile is immutable per domain

When creating a domain, persist an embedding snapshot:

```json
{
  "profile_id": "openai-text-embedding-3-large",
  "provider": "openai",
  "binding": "openai",
  "base_url": "https://api.openai.com/v1",
  "model": "text-embedding-3-large",
  "dimensions": 3072,
  "token_limit": 8192,
  "fingerprint": "openai:text-embedding-3-large:3072"
}
```

After the domain exists, do not allow changing this value.

### Rule 4: LLM default can change

Changing the default LLM should affect:

- future domain.env generation
- future LightRAG domain creation
- future query/answer-generation paths that use the app default LLM

Changing LLM should not require re-embedding. However, warn admins that changing LLMs may affect future graph extraction style and answer quality.

### Rule 5: Legacy domains need explicit status

For existing domains without embedding snapshots, show:

```text
Legacy embedding config
```

Actions:

- if domain has no indexed documents, allow assigning an embedding profile once
- if domain has indexed documents, show read-only warning and recommend rebuild/recreate

## UX Summary

Add a settings route:

```text
Settings
  Account
  Knowledge Graphs
  AI Models        admin only
```

The `AI Models` page should have three cards:

1. Current defaults
2. LLM profiles
3. Embedding profiles

The domain creation dialog should include:

```text
Embedding model
[ text-embedding-3-small · OpenAI · 1536 dims ▼ ]

This will be locked after creation. Changing embedding models later requires rebuilding the knowledge graph.
```

## Non-Goals for V1

- No user-specific model preferences.
- No raw API key editing in browser.
- No automatic provider model discovery required.
- No Bedrock native embedding provider unless explicitly added later.
- No per-document embedding model selection.
- No ability to mix embedding profiles inside one domain.
