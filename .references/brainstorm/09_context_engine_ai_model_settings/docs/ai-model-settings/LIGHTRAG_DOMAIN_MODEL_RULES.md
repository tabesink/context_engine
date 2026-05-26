# LightRAG Domain Model Rules

## Current Problem

LightRAG domain creation currently accepts a simple create request with domain id, display name, host port, and default flag. Provider information is currently configured through root environment/example files and generated `domain.env` files.

This needs to change so that each domain records the exact embedding profile used at creation time.

## Required Domain Create Request

Extend:

```python
class LightRAGDomainCreateRequest(BaseModel):
    domain_id: str
    display_name: str | None = None
    host_port: int | None = None
    make_default: bool = False
    embedding_profile_id: str | None = None
    llm_profile_id: str | None = None
```

Rules:

- `embedding_profile_id` defaults to current default embedding profile.
- `llm_profile_id` defaults to current default LLM profile.
- embedding profile is snapshotted into domain manifest.
- LLM profile may be snapshotted or may inherit current default; recommended V1 is to snapshot the LLM profile ID but allow regeneration with new default only if `llm_inherits_default=true`.

## Domain Manifest Extension

Extend `LightRAGDomain` with:

```python
class DomainModelSnapshot(BaseModel):
    profile_id: str
    provider: str
    binding: str
    base_url: str
    model: str
    api_key_env_var: str | None = None
    dimensions: int | None = None
    token_limit: int | None = None
    send_dimensions: bool = False
    use_base64: bool = True
    fingerprint: str

class LightRAGDomain(BaseModel):
    ...
    embedding: DomainModelSnapshot | None = None
    llm: DomainModelSnapshot | None = None
    llm_inherits_default: bool = True
```

Do not include raw secrets in manifest API responses.

## Domain.env Generation

Update:

```text
app/lightrag_deploy/compose.py
```

`render_domain_env()` should append model values.

For OpenAI embedding:

```env
EMBEDDING_BINDING=openai
EMBEDDING_BINDING_HOST=https://api.openai.com/v1
EMBEDDING_BINDING_API_KEY=<resolved secret>
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIM=3072
EMBEDDING_TOKEN_LIMIT=8192
EMBEDDING_SEND_DIM=false
EMBEDDING_USE_BASE64=true
```

For Ollama embedding:

```env
EMBEDDING_BINDING=ollama
EMBEDDING_BINDING_HOST=http://host.docker.internal:11434
EMBEDDING_BINDING_API_KEY=ollama
EMBEDDING_MODEL=bge-m3
EMBEDDING_DIM=<configured dimension>
EMBEDDING_TOKEN_LIMIT=8192
```

For OpenAI LLM:

```env
LLM_BINDING=openai
LLM_BINDING_HOST=https://api.openai.com/v1
LLM_BINDING_API_KEY=<resolved secret>
LLM_MODEL=gpt-4o-mini
```

For Bedrock OpenAI-compatible LLM:

```env
LLM_BINDING=openai
LLM_BINDING_HOST=https://bedrock-mantle.us-east-1.api.aws/v1
LLM_BINDING_API_KEY=<AWS_BEARER_TOKEN_BEDROCK>
LLM_MODEL=openai.gpt-oss-120b
```

For Ollama LLM:

```env
LLM_BINDING=ollama
LLM_BINDING_HOST=http://host.docker.internal:11434
LLM_BINDING_API_KEY=ollama
LLM_MODEL=qwen3:8b
```

Note: whether Ollama LightRAG binding expects `/v1` depends on binding type. If using `LLM_BINDING=ollama`, configure host according to LightRAG's Ollama binding expectations. If using OpenAI-compatible mode for Ollama, use `LLM_BINDING=openai` and `http://host.docker.internal:11434/v1`. Pick one style and test it.

## Embedding Lock

After domain creation:

```text
domain.embedding.fingerprint is immutable.
```

Do not allow:

- changing provider
- changing model
- changing dimensions
- changing token limit if it affects embedding behavior
- uploading documents with a different profile
- regenerating domain.env with a different embedding profile

Allow:

- re-rendering domain.env using the same embedding profile
- updating API key values from environment
- changing LLM profile
- changing LLM base URL/model for future operations

## Existing Domains

For existing domains without embedding snapshot:

### Empty domain

Allow admin to assign embedding profile once.

### Non-empty domain

Mark as legacy. Recommend recreate/rebuild.

UI text:

```text
This domain was created before model locking. Its embedding model is not recorded. Do not change embedding settings for this domain unless you rebuild it.
```

## Domain Creation Flow

```text
POST /admin/lightrag/domains
  → require admin
  → resolve embedding profile from request or default
  → validate embedding profile enabled
  → resolve LLM profile from request or default
  → create immutable embedding snapshot
  → create optional LLM snapshot/default reference
  → create LightRAG domain manifest
  → render domain.env
  → write compose file
  → audit event
```

## Upload Flow

```text
POST /admin/documents/upload
  → require admin
  → require domain id
  → load domain
  → ensure domain has embedding snapshot
  → upload/index document
```

Do not expose embedding profile selection during document upload. It belongs to the domain, not the document.
