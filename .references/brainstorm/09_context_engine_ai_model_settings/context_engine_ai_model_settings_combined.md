# Context Engine AI Model Settings Implementation Package



---

# README.md

# AI Model Settings Documentation Package

Generated: 2026-05-26

This package describes the implementation plan for adding an **admin-only AI Models settings shell** to `context_engine`.

The feature lets an admin select default LLM and embedding profiles, then uses those profiles in LightRAG domain creation and other backend workflows.

## Core Decision

Embedding model selection is **domain-locked**.

LLM selection is **default-driven and changeable**.

```text
Admin Settings
  → AI Models
      → default LLM profile
      → default embedding profile
      → allowed embedding profiles
  → Create Knowledge Graph / LightRAG Domain
      → choose embedding profile once
      → persist immutable embedding snapshot on domain
      → generate LightRAG domain.env from that snapshot
```

## Files in This Package

- `FEATURE_SPEC.md` — product behavior and UX rules.
- `BACKEND_IMPLEMENTATION.md` — API, schema, services, migrations, validation.
- `FRONTEND_IMPLEMENTATION.md` — settings shell UI, admin-only flows, domain creation UX.
- `LIGHTRAG_DOMAIN_MODEL_RULES.md` — embedding immutability and domain.env generation.
- `CODING_AGENT_TASKS.md` — task-sized implementation plan.
- `ADRS_TO_WRITE.md` — architecture decisions to preserve.
- `RESEARCH_NOTES.md` — official-doc notes and source links.

## Recommended Implementation Order

1. Add backend schema and service layer for AI model profiles.
2. Add admin-only API routes.
3. Extend LightRAG domain model with immutable embedding snapshot.
4. Update domain.env generation.
5. Add frontend settings shell route: `Settings → AI Models`.
6. Add embedding dropdown to Knowledge Graph / LightRAG domain creation.
7. Add tests and migration.


---

# FEATURE_SPEC.md

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


---

# BACKEND_IMPLEMENTATION.md

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


---

# LIGHTRAG_DOMAIN_MODEL_RULES.md

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


---

# FRONTEND_IMPLEMENTATION.md

# Frontend Implementation Plan

## Current Frontend Context

The client is a Next.js app using React, TypeScript, Tailwind, Radix UI components, lucide-react icons, and existing admin settings under `client/src/app/settings/users/page.tsx`.

The new UI should match the existing app style:

- muted neutral surfaces
- rounded cards
- compact tables
- shadcn/Radix-style controls
- badges for status
- clear admin-only routing
- minimal visual noise
- explicit warnings for destructive or irreversible choices

## New Settings Shell

Create:

```text
client/src/app/settings/layout.tsx
client/src/app/settings/models/page.tsx
client/src/api/ai-settings.ts
client/src/types/ai-settings.ts
```

The layout should provide a left rail:

```text
Settings
  Account
  Knowledge Graphs
  AI Models     admin only
```

If only admins can access settings for now, still keep `AI Models` hidden or disabled for non-admins.

## AI Models Page Layout

Recommended page structure:

```text
AI Models
Configure default LLM and embedding profiles used by Context Engine and new Knowledge Graph domains.

[Current Defaults]
  Default LLM:       OpenAI · gpt-4o-mini             [Change]
  Default Embedding: OpenAI · text-embedding-3-small  [Change]
  Note: Embedding changes only affect new domains.

[LLM Profiles]
  Provider      Model                 Endpoint       Status       Default
  OpenAI        gpt-4o-mini           api.openai     Ready        ✓
  Bedrock       openai.gpt-oss-120b   us-east-1      Missing key
  Ollama        qwen3:8b              local          Offline

[Embedding Profiles]
  Provider      Model                    Dims   Token limit   Status   Default
  OpenAI        text-embedding-3-small   1536   8192          Ready    ✓
  OpenAI        text-embedding-3-large   3072   8192          Ready
  Ollama        bge-m3                   1024   8192          Offline
```

## UX Copy

Top description:

```text
Admins can choose the default LLM and embedding model. Embeddings are locked to each knowledge graph at creation time to avoid mixing vector spaces.
```

Embedding warning card:

```text
Embedding model changes are not retroactive.
Existing knowledge graphs keep the embedding model they were created with. To change embeddings for an existing graph, create a new graph or rebuild the domain.
```

LLM info card:

```text
LLM defaults can be changed without rebuilding vectors. They affect future answer generation and future graph extraction behavior.
```

## Profile Row Actions

Per row actions:

```text
Set as default
Test connection
Edit
Disable
```

Disable rules:

- cannot disable the current default profile
- cannot disable a profile used by an active domain without warning
- can disable unused profiles

## Connection Status

Use status badges:

```text
Ready
Missing key
Offline
Invalid dimensions
Untested
```

Do not show raw secret values.

## Domain Creation UX

Update the Knowledge Graph / LightRAG domain creation form.

Add section:

```text
Embedding model

[ OpenAI · text-embedding-3-small · 1536 dims ▼ ]

Locked after creation.
All documents in this knowledge graph must use the same embedding model. Changing this later requires rebuilding the graph.
```

Add optional advanced section:

```text
LLM model

[ Use current default: OpenAI · gpt-4o-mini ▼ ]

The LLM can be changed later. The embedding model cannot.
```

Recommended defaults:

- embedding dropdown preselects global default embedding profile
- LLM dropdown preselects "Use current default"
- if admin picks explicit LLM profile, store it as domain override

## Domain List UX

In domain cards/table, show:

```text
Embedding: text-embedding-3-small · 1536 dims · locked
LLM: Default · gpt-4o-mini
```

For legacy domains:

```text
Embedding: Legacy / unknown
```

Badge color should communicate caution, not panic.

## Admin-Only Access

Use existing auth store:

```ts
selectIsAdmin
```

In page effect:

```ts
if (!isAdmin) router.replace("/chat");
```

Also rely on backend `require_admin`; frontend hiding is not security.

## API Client

Create:

```ts
client/src/api/ai-settings.ts
```

Functions:

```ts
export async function getAISettings(): Promise<AISettingsResponse>
export async function updateAISettingsDefaults(payload: UpdateDefaultsPayload): Promise<AISettingsResponse>
export async function createAIModelProfile(payload: CreateProfilePayload): Promise<AIModelProfile>
export async function updateAIModelProfile(id: string, payload: UpdateProfilePayload): Promise<AIModelProfile>
export async function testAIModelProfile(id: string): Promise<ModelProfileTestResult>
```

## Types

```ts
export type ProviderKind = "openai" | "bedrock_openai" | "ollama";
export type ModelProfileKind = "llm" | "embedding";

export type AIModelProfile = {
  id: string;
  kind: ModelProfileKind;
  provider: ProviderKind;
  display_name: string;
  model: string;
  base_url: string;
  dimensions: number | null;
  token_limit: number | null;
  is_enabled: boolean;
  is_default: boolean;
  api_key_status: "present" | "missing" | "not_required";
};
```

## Accessibility and UX Rules

- All dropdowns require labels.
- Dangerous/irreversible rules need helper text.
- Do not use only color for status.
- Disable buttons with explanation text.
- Use confirmation dialog when disabling profile used by domains.
- Keep tables compact but readable.
- Use cards for conceptual separation.

## Empty States

No profiles:

```text
No model profiles configured. Seed defaults or create a profile.
```

Missing API key:

```text
OPENAI_API_KEY is not configured on the server. Add it to the backend environment and restart the API.
```

Ollama offline:

```text
Could not reach Ollama. Confirm Ollama is running and accessible from the backend container.
```


---

# CODING_AGENT_TASKS.md

# Coding Agent Implementation Tasks

## Phase 0: Safety and Design Alignment

### Task 0.1 — Add ADR

Create:

```text
docs/adr/ADR-ai-model-settings-and-domain-embedding-lock.md
```

Acceptance criteria:

- explains embedding immutability
- explains LLM mutability
- explains admin-only control
- explains why raw secrets stay out of browser

## Phase 1: Backend Schema

### Task 1.1 — Add AI model domain models

Files:

```text
app/domain/ai_models.py
app/schemas/ai_settings.py
```

Acceptance criteria:

- provider enums exist
- request/response schemas exist
- response schemas redact secrets

### Task 1.2 — Add DB migration

Files:

```text
migrations/versions/<timestamp>_add_ai_model_settings.py
app/storage/tables.py
```

Acceptance criteria:

- `ai_model_profiles` table exists
- `ai_model_settings` table exists
- migration upgrades and downgrades cleanly
- tests use new schema without failing

## Phase 2: Backend Services and API

### Task 2.1 — Add repository

Files:

```text
app/storage/repositories/ai_model_settings.py
```

Acceptance criteria:

- CRUD profiles
- get/set defaults
- list enabled profiles
- no raw secret values stored

### Task 2.2 — Add service

Files:

```text
app/services/ai_model_settings_service.py
app/services/model_profile_resolver.py
```

Acceptance criteria:

- can seed default profiles
- validates profile kind/provider
- checks secret env var status
- resolves LightRAG env config
- computes embedding fingerprint

### Task 2.3 — Add admin route

Files:

```text
app/api/routes/ai_settings.py
app/main.py
```

Acceptance criteria:

- `/admin/ai-settings` routes registered
- all routes require admin
- regular user receives 403/401
- secrets redacted

## Phase 3: LightRAG Domain Integration

### Task 3.1 — Extend domain models

Files:

```text
app/lightrag_deploy/models.py
```

Acceptance criteria:

- create request accepts `embedding_profile_id`
- domain manifest includes embedding snapshot
- existing domain manifests still load

### Task 3.2 — Wire profile resolution into domain creation

Files:

```text
app/api/routes/lightrag_admin.py
app/lightrag_deploy/service.py
```

Acceptance criteria:

- domain creation uses requested/default embedding profile
- embedding snapshot persisted
- LLM profile persisted or inherited
- audit log records profile IDs

### Task 3.3 — Render domain.env from profile snapshots

Files:

```text
app/lightrag_deploy/compose.py
```

Acceptance criteria:

- generated domain.env includes LLM settings
- generated domain.env includes embedding settings
- existing storage settings are preserved
- no profile change mutates existing domain embedding snapshot

## Phase 4: Frontend Settings Shell

### Task 4.1 — Add settings layout

Files:

```text
client/src/app/settings/layout.tsx
```

Acceptance criteria:

- left rail with Account, Knowledge Graphs, AI Models
- AI Models visible only to admins
- layout matches existing app style

### Task 4.2 — Add AI Models page

Files:

```text
client/src/app/settings/models/page.tsx
client/src/api/ai-settings.ts
client/src/types/ai-settings.ts
```

Acceptance criteria:

- admin can view defaults
- admin can set default LLM
- admin can set default embedding
- status badges show key/missing/offline state
- helper text explains embedding lock

## Phase 5: Domain Creation UI

### Task 5.1 — Add embedding dropdown

Files depend on current domain creation UI location.

Acceptance criteria:

- dropdown populated from enabled embedding profiles
- default selected
- helper text says locked after creation
- request sends `embedding_profile_id`

### Task 5.2 — Show domain model summary

Acceptance criteria:

- domain cards/table show embedding model and dims
- legacy domains show warning
- LLM default/override shown

## Phase 6: Tests

### Backend tests

Add:

```text
tests/test_ai_settings_api.py
tests/test_ai_model_settings_service.py
tests/test_lightrag_domain_model_lock.py
```

Required tests:

- non-admin cannot access settings
- default profiles can be changed by admin
- profile with missing secret cannot be set active unless allowed
- new domain snapshots embedding profile
- existing domain snapshot does not change when default changes
- generated domain.env includes expected values

### Frontend tests

If frontend test framework exists:

- admin sees AI Models nav
- non-admin does not
- embedding dropdown helper text appears
- save/default flow handles API errors

## Phase 7: Documentation

Update:

```text
README.md
.env.example
.env.lightrag-provider.example
docs/ai-model-settings/
```

Acceptance criteria:

- provider profile setup documented
- OpenAI, Bedrock OpenAI-compatible, and Ollama examples included
- warning against mixing embeddings included
- secret handling documented

## Rollback Plan

If issues appear:

1. keep old `.env.lightrag-provider.example` behavior
2. disable `/admin/ai-settings` route from `app/main.py`
3. domain creation falls back to existing env-driven config
4. no migration rollback unless tables break startup

Do not roll back domain manifests without backing up `.data/lightrag/domains.json`.


---

# ADRS_TO_WRITE.md

# ADRs to Write

## ADR: AI Model Settings and Domain Embedding Lock

### Decision

The app stores admin-selectable AI model profiles.

Embedding profiles are immutable per LightRAG domain after creation.

LLM defaults can be changed.

### Context

Embedding vectors from different models are not compatible inside the same vector index. LightRAG also requires the embedding model and dimension to be decided before indexing.

### Consequences

- Domain creation must snapshot embedding profile.
- Domain upload must use domain embedding profile.
- Existing domains do not automatically change when admin changes default embedding.
- To change embedding model, rebuild/recreate domain.
- LLM changes can be applied more flexibly.

## ADR: Secrets Stay in Environment, Not Browser

### Decision

The admin UI can select profiles and show secret status, but it cannot read or write raw API keys in V1.

### Consequences

- Safer implementation.
- Less risk of accidental secret disclosure.
- Admin must configure keys in `.env` or deployment secret manager.

## ADR: Provider Scope for V1

### Decision

V1 exposes:

- OpenAI LLM
- AWS Bedrock OpenAI-compatible LLM
- Ollama LLM
- OpenAI embeddings
- Ollama embeddings

### Consequences

- Bedrock native embeddings are deferred.
- Future native Bedrock embeddings require separate adapter and UI profile type.


---

# RESEARCH_NOTES.md

# Research Notes

## OpenAI Embeddings

OpenAI's docs describe `text-embedding-3-small` and `text-embedding-3-large` as current embedding models. Defaults:

- `text-embedding-3-small`: 1536 dimensions
- `text-embedding-3-large`: 3072 dimensions
- both list 8192 max input in the OpenAI embeddings guide

Source:

- https://developers.openai.com/api/docs/guides/embeddings

## Ollama OpenAI Compatibility

Ollama documents partial OpenAI API compatibility and supports:

- `/v1/chat/completions`
- `/v1/responses`
- `/v1/models`
- `/v1/embeddings`

For local OpenAI SDK compatibility, the API key is required by SDK shape but ignored by Ollama.

Source:

- https://docs.ollama.com/api/openai-compatibility

## AWS Bedrock OpenAI-Compatible APIs

Amazon Bedrock documents OpenAI-compatible Chat Completions and Responses APIs. The OpenAI SDK must point to the Bedrock endpoint and use an Amazon Bedrock API key.

Examples:

- Chat Completions endpoint: `https://bedrock-runtime.<region>.amazonaws.com/openai/v1`
- Responses API endpoint: `https://bedrock-mantle.<region>.api.aws/v1`

Sources:

- https://docs.aws.amazon.com/bedrock/latest/userguide/inference-chat-completions.html
- https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-mantle.html

## Bedrock Embeddings

Amazon Bedrock has native embedding models such as Titan Text Embeddings V2. These are not the same as exposing OpenAI `/v1/embeddings` through the Bedrock OpenAI-compatible path.

Source:

- https://docs.aws.amazon.com/bedrock/latest/userguide/titan-embedding-models.html

## LightRAG Provider and Embedding Rules

LightRAG docs state that LLM and embedding providers must be configured before server startup and that LightRAG supports OpenAI-compatible, Ollama, Bedrock, and other bindings. The LightRAG README also warns that the embedding model must be determined before document indexing and the same model must be used during query; for storage like PostgreSQL, vector dimensions are defined at table creation.

Sources:

- https://github.com/HKUDS/LightRAG/blob/main/docs/LightRAG-API-Server.md
- https://github.com/HKUDS/LightRAG
- https://github.com/HKUDS/LightRAG/blob/main/env.example
