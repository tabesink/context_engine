# Provider Settings Review

## Desired Behavior

Admin should be able to configure Provider settings from the Settings dialog.

Provider settings should include:

```text
provider type
base URL
API key / credential
default LLM model
default embedding model
allowed LLM models
allowed embedding models
connection/configuration status
```

The Settings route should be named:

```text
Provider
```

not:

```text
LLM Model
```

## Current Positive Findings

The modified codebase now includes:

- frontend Settings route labeled `Provider`
- `AIModelSettingsPanel`
- API client for `/admin/ai-settings`
- backend router `/admin/ai-settings`
- backend schemas for AI model profiles and settings
- encrypted provider secret repository
- provider kinds for OpenAI, Bedrock OpenAI-compatible, and Ollama

## Current Gaps

### Gap 1: Route Store Type Needs Update

The UI route registry uses `provider`, but the settings route store may still use `ai-models`.

Required change:

```ts
type SettingsRoute = "general" | "account" | "knowledge-graph" | "provider";
```

### Gap 2: Provider UI Does Not Expose Full Profile Management

The backend API supports creating/updating/testing profiles, but the visible settings panel appears focused on:

- default LLM profile selection
- default embedding profile selection
- provider secret entry

It may not expose:

- create custom profile
- update base URL per profile
- update model name per profile
- test selected profile
- disable profile
- allowed models by provider

Recommendation:

For the next pass, keep UI simple:

```text
Provider Settings
  → Provider secrets
  → Default LLM profile
  → Default embedding profile
  → Test selected/default profile
```

Add profile create/edit later if needed.

### Gap 3: Test Connection Is Not a Real Provider Test

The backend service appears to validate secret presence but not call the provider.

Recommendation:

Either:

```text
Rename to "Validate configuration"
```

or implement actual provider health checks.

## Recommended Backend Provider Model

Use this conceptually:

```text
AIModelProfile
  id
  kind: llm | embedding
  provider: openai | bedrock_openai | ollama
  label
  model
  base_url
  api_key_env_var
  dimensions
  token_limit
  is_active
  created_at
  updated_at
```

Use a separate secret store:

```text
AIProviderSecret
  secret_name
  encrypted_value
  updated_at
```

Frontend responses should expose:

```text
api_key_status: missing | configured | env
```

Never expose raw keys.

## Admin/User Boundary

Provider config endpoints must be admin-only.

Required tests:

- admin can read settings
- regular user cannot read settings
- admin can update defaults
- regular user cannot update defaults
- admin can set secret
- secret response is masked
- raw key never appears in JSON response
