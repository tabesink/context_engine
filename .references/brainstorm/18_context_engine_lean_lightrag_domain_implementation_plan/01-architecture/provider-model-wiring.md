# Provider and Model Wiring

## Current responsibility split

AI Settings owns:

```text
ai_model_profiles
ai_model_settings
ai_provider_secrets
```

LightRAG Domains owns:

```text
domain identity
embedding model snapshot
runtime artifact generation
Docker startup
```

## Lean rule

Do not duplicate provider/model settings into random lifecycle code. Add one internal resolver that produces the runtime config required to write `domain.env`.

## Recommended internal service

Create a focused internal service:

```python
class LightRAGRuntimeConfigResolver:
    def resolve_for_domain_start(self, domain: LightRAGDomain) -> LightRAGRuntimeConfig:
        ...
```

It should resolve:

```text
LLM runtime config
Embedding runtime config
Provider secret values
Postgres runtime config
Retrieval defaults from backend settings
```

## Runtime config object

Suggested shape:

```python
@dataclass(frozen=True)
class ResolvedModelRuntime:
    profile_id: str | None
    provider: str
    binding: str
    model: str
    base_url: str | None
    api_key_env_var: str | None
    api_key_value: str | None
    dimensions: int | None = None
    token_limit: int | None = None

@dataclass(frozen=True)
class LightRAGRuntimeConfig:
    llm: ResolvedModelRuntime
    embedding: ResolvedModelRuntime
    retrieval_defaults: LightRAGRetrievalEnvDefaults
    postgres: LightRAGPostgresRuntimeConfig | None
```

## Embedding profile rule

The domain embedding model is selected at Create time and stored as a snapshot in the domain manifest.

After first successful ingestion, treat it as locked.

```text
New embedding model needed -> create new domain
Provider API key changed -> restart same domain
```

## LLM profile rule

Pick one explicit policy.

Recommended:

```text
Use AI Settings default LLM profile when writing domain.env.
```

This means Start uses the latest default LLM/profile/secret values.

## Restart-required rule

When provider secrets or model profiles change, running domains should be marked as needing restart or at least display a notice.

Minimum viable implementation:

```text
After provider secret save:
  show UI notice: Running LightRAG domains must be restarted to use the new value.
```

Better implementation:

```text
provider_config_revision increments
running domains compare applied revision
needs_restart = provider_config_revision > applied_revision
```
