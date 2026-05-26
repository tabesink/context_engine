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
