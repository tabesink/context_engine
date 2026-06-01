# 07 — Provider Configuration Plan

## Recommended Decision

For the lean Context Engine app, provider config should be environment/domain-level by default.

```text
.env / domain.env = source of truth
Database provider profiles = optional advanced mode
Provider UI = diagnostics, not broad runtime mutation
```

## Why

Runtime-editable provider profiles are powerful, but they increase complexity:

```text
more tables
secret encryption/decryption path
more validation states
more UI states
more ways ingestion/retrieval can disagree
harder debugging for junior devs
```

For a 5–10 user app, static config is simpler, safer, and easier to debug.

## Lean Provider Rules

```text
Embedding model is fixed per domain at domain creation.
Retrieval defaults are not runtime-editable.
Provider keys come from env/secrets manager/domain.env.
Provider UI shows current resolved config and health status.
Provider UI can test connectivity.
Provider UI should not imply runtime editing unless that mode is intentionally enabled.
```

## Backend Target

Create or clarify one service:

```text
ProviderConfigService
```

Responsibilities:

```text
resolve current LLM provider
resolve current embedding provider
resolve domain embedding model
validate required keys/config
expose diagnostics-safe provider summary
run provider connectivity tests
```

It should hide whether config came from:

```text
.env
domain.env
DB profile
secret table
```

## Provider Diagnostics Response

Target shape:

```json
{
  "mode": "env|database|mixed",
  "llm": {
    "provider": "openai|ollama|bedrock_openai_compatible",
    "model": "string",
    "base_url": "string-or-null",
    "status": "configured|missing_key|local"
  },
  "embedding": {
    "provider": "openai|ollama|bedrock_openai_compatible",
    "model": "string",
    "fixed_per_domain": true
  },
  "domains": [
    {
      "domain_id": "string",
      "embedding_model": "string"
    }
  ]
}
```

Do not return raw secrets.

## Frontend Provider Page

Provider page should show:

```text
Current LLM provider
Current embedding provider
Current model names
Missing key / local indicators
Domain embedding model table
Test connection button
```

Remove or hide:

```text
runtime retrieval defaults
embedding default changes after domain creation
advanced profile mutation unless intentionally retained
```

## Migration Strategy

1. Keep existing `/admin/ai-settings` working.
2. Add provider diagnostics endpoint or map existing data into diagnostics.
3. Update frontend to read diagnostics.
4. Hide runtime mutation controls.
5. Later, remove unused DB profile paths only if no longer used.
