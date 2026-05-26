# Backend Implementation Plan

## New Backend Modules

Add:

```text
app/domain/ai_models.py
app/schemas/ai_settings.py
app/storage/repositories/ai_model_settings.py
app/services/ai_model_settings_service.py
app/services/model_profile_resolver.py
app/api/routes/ai_settings.py
```

Register route in:

```text
app/main.py
```

## Domain Types

Create explicit domain enums:

```python
ProviderKind = Literal["openai", "bedrock_openai", "ollama"]
ModelProfileKind = Literal["llm", "embedding"]
```

Recommended profile shape:

```python
class AIModelProfile(BaseModel):
    id: str
    kind: Literal["llm", "embedding"]
    provider: Literal["openai", "bedrock_openai", "ollama"]
    display_name: str
    model: str
    base_url: str
    api_key_env_var: str | None = None
    binding: str
    dimensions: int | None = None
    token_limit: int | None = None
    send_dimensions: bool = False
    use_base64: bool = True
    is_enabled: bool = True
    is_default: bool = False
    extra: dict = {}
```

## Database Tables

Add migration for:

```text
ai_model_profiles
ai_model_settings
```

### `ai_model_profiles`

```text
id                   string primary key
kind                 string not null      -- llm | embedding
provider             string not null      -- openai | bedrock_openai | ollama
display_name         string not null
model                string not null
base_url             string not null
api_key_env_var      string nullable
binding              string not null      -- LightRAG binding, e.g. openai or ollama
dimensions           integer nullable
token_limit          integer nullable
send_dimensions      boolean default false
use_base64           boolean default true
is_enabled           boolean default true
extra                json default {}
created_at           datetime
updated_at           datetime
```

### `ai_model_settings`

Simplest form:

```text
id                            integer primary key, always 1
default_llm_profile_id         string foreign key ai_model_profiles.id
default_embedding_profile_id   string foreign key ai_model_profiles.id
updated_by_user_id             string nullable
updated_at                     datetime
```

Alternative simpler V1: store `is_default=true` on profile rows and enforce one default per kind in service code. The separate `ai_model_settings` table is clearer for junior developers.

## Admin API

Add admin-only routes:

```text
GET    /admin/ai-settings
PUT    /admin/ai-settings/defaults
POST   /admin/ai-settings/profiles
PATCH  /admin/ai-settings/profiles/{profile_id}
POST   /admin/ai-settings/profiles/{profile_id}/test
```

### GET `/admin/ai-settings`

Returns:

```json
{
  "defaults": {
    "llm_profile_id": "openai-gpt-4o-mini",
    "embedding_profile_id": "openai-text-embedding-3-small"
  },
  "profiles": [
    {
      "id": "openai-text-embedding-3-small",
      "kind": "embedding",
      "provider": "openai",
      "display_name": "OpenAI text-embedding-3-small",
      "model": "text-embedding-3-small",
      "base_url": "https://api.openai.com/v1",
      "api_key_status": "present",
      "dimensions": 1536,
      "token_limit": 8192,
      "is_enabled": true,
      "is_default": true
    }
  ],
  "secret_status": {
    "OPENAI_API_KEY": "present",
    "AWS_BEARER_TOKEN_BEDROCK": "missing"
  }
}
```

Never return raw secrets.

### PUT `/admin/ai-settings/defaults`

Request:

```json
{
  "default_llm_profile_id": "bedrock-gpt-oss-120b",
  "default_embedding_profile_id": "openai-text-embedding-3-large"
}
```

Validation:

- profile exists
- profile enabled
- LLM default points to `kind=llm`
- embedding default points to `kind=embedding`
- embedding provider is allowed in V1
- required secret env var is present unless provider is Ollama

### POST/PATCH profile routes

Allow admins to maintain curated profile list.

For V1, allow:

- display name
- model
- base URL
- env var name
- dimensions/token limit for embeddings
- enabled flag

Do not allow raw API key values.

### POST profile test

For LLM profile:

- call a tiny chat/completions or responses request depending on provider mode
- use short timeout
- return success/failure and sanitized error

For embedding profile:

- call embeddings for `"health check"`
- verify returned vector length matches configured dimensions when dimensions is set
- return vector length

## Service Layer

### `AIModelSettingsService`

Responsibilities:

- list profiles
- create/update profiles
- set defaults
- seed defaults if empty
- validate provider-specific constraints
- redact secrets
- test profiles
- audit changes

### `ModelProfileResolver`

Responsibilities:

- resolve active default LLM profile
- resolve active default embedding profile
- resolve explicit embedding profile by ID
- convert profile to LightRAG env values
- compute embedding fingerprint

Example fingerprint:

```python
def embedding_fingerprint(profile: AIModelProfile) -> str:
    return f"{profile.provider}:{profile.model}:{profile.dimensions or 'unknown'}"
```

## Seeding Defaults

Add seed function:

```text
scripts/seed_ai_model_profiles.py
```

or run inside migration/service initialization.

Prefer explicit script for low magic.

Seed profiles from `.env.example` defaults, but store only env var names, not secrets.

## App Settings Additions

Add to `app/core/config.py`:

```python
openai_api_key: str | None = None
aws_bearer_token_bedrock: str | None = None
ollama_base_url: str = "http://host.docker.internal:11434/v1"

default_openai_base_url: str = "https://api.openai.com/v1"
default_bedrock_openai_base_url: str | None = None
```

Do not overstuff `Settings` with all model profiles. The DB should own admin-editable profiles.

## Audit Events

Record:

```text
ai_settings.defaults.updated
ai_model_profile.created
ai_model_profile.updated
ai_model_profile.disabled
ai_model_profile.tested
lightrag.domain.created_with_embedding_profile
```

Do not log secrets.

## Tests

Add tests:

```text
tests/test_ai_settings_api.py
tests/test_ai_model_settings_service.py
tests/test_model_profile_resolver.py
tests/test_lightrag_domain_embedding_lock.py
```

Minimum acceptance tests:

- non-admin cannot access `/admin/ai-settings`
- admin can list settings
- admin can set default LLM
- admin can set default embedding
- cannot set disabled profile as default
- cannot set LLM profile as embedding default
- cannot create embedding profile without dimensions unless provider profile explicitly allows unknown dimension
- domain creation persists embedding snapshot
- changing default embedding does not mutate existing domain snapshot
- domain.env includes the domain snapshot embedding values
