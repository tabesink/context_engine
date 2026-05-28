# Recommended Frontend Folder Structure

This structure is designed for a Next.js/React + shadcn application where design changes are implemented surface-by-surface while preserving API contracts.

## Repository-level structure

```txt
context_engine/
├── frontend/
│   ├── app/                         # Next.js routes / route groups
│   ├── components/                  # Shared UI and app-level components
│   ├── features/                    # Feature-owned UI, hooks, API clients, types
│   ├── lib/                         # Cross-cutting frontend utilities
│   ├── styles/                      # Global CSS and design tokens
│   └── tests/                       # Frontend test and Playwright specs
├── backend/                         # Existing FastAPI backend
├── docs/
│   └── design/                      # Product-wide design docs
├── specs/                           # Per-surface implementation specs
├── agents/                          # Reusable coding-agent prompts
├── mcp/                             # MCP config examples / setup notes
└── .cursor/
    └── rules/                       # Cursor/coding-agent rules
```

## Frontend structure

```txt
frontend/
├── app/
│   ├── (auth)/
│   │   └── login/
│   │       └── page.tsx
│   ├── (app)/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── chat/
│   │   │   └── page.tsx
│   │   ├── domains/
│   │   │   └── page.tsx
│   │   ├── documents/
│   │   │   └── page.tsx
│   │   ├── providers/
│   │   │   └── page.tsx
│   │   └── settings/
│   │       ├── layout.tsx
│   │       ├── page.tsx
│   │       └── providers/
│   │           └── page.tsx
│   └── api/                         # Only if frontend route handlers are needed
│
├── components/
│   ├── ui/                          # shadcn generated primitives only
│   ├── app/                         # app shell components shared across routes
│   │   ├── app-sidebar.tsx
│   │   ├── app-topbar.tsx
│   │   ├── page-header.tsx
│   │   ├── section-card.tsx
│   │   ├── status-badge.tsx
│   │   ├── empty-state.tsx
│   │   └── confirm-action.tsx
│   ├── layout/
│   │   ├── two-pane-layout.tsx
│   │   ├── settings-shell.tsx
│   │   └── workspace-shell.tsx
│   └── feedback/
│       ├── loading-panel.tsx
│       ├── error-panel.tsx
│       └── permission-panel.tsx
│
├── features/
│   ├── auth/
│   │   ├── api.ts
│   │   ├── hooks.ts
│   │   ├── types.ts
│   │   └── components/
│   ├── providers/
│   │   ├── api.ts
│   │   ├── hooks.ts
│   │   ├── schemas.ts
│   │   ├── types.ts
│   │   └── components/
│   │       ├── provider-card.tsx
│   │       ├── provider-config-form.tsx
│   │       ├── provider-status-panel.tsx
│   │       └── provider-model-table.tsx
│   ├── domains/
│   │   ├── api.ts
│   │   ├── hooks.ts
│   │   ├── types.ts
│   │   └── components/
│   │       ├── domain-card.tsx
│   │       ├── domain-actions-menu.tsx
│   │       ├── domain-health-panel.tsx
│   │       └── domain-lifecycle-table.tsx
│   ├── documents/
│   │   ├── api.ts
│   │   ├── hooks.ts
│   │   ├── types.ts
│   │   └── components/
│   │       ├── upload-dropzone.tsx
│   │       ├── document-status-card.tsx
│   │       ├── document-job-timeline.tsx
│   │       └── document-table.tsx
│   ├── chat/
│   │   ├── api.ts
│   │   ├── hooks.ts
│   │   ├── types.ts
│   │   └── components/
│   │       ├── chat-composer.tsx
│   │       ├── retrieval-settings.tsx
│   │       ├── evidence-card.tsx
│   │       └── context-panel.tsx
│   └── source-navigation/
│       ├── types.ts
│       └── components/
│           ├── source-detail-panel.tsx
│           ├── figure-card.tsx
│           └── table-card.tsx
│
├── lib/
│   ├── api/
│   │   ├── client.ts
│   │   ├── errors.ts
│   │   └── query-keys.ts
│   ├── design/
│   │   ├── tokens.ts
│   │   └── variants.ts
│   ├── permissions.ts
│   ├── cn.ts
│   └── utils.ts
│
├── styles/
│   └── globals.css
│
└── tests/
    ├── e2e/
    │   ├── providers.spec.ts
    │   ├── domains.spec.ts
    │   ├── documents.spec.ts
    │   └── chat-context-panel.spec.ts
    └── fixtures/
        ├── providers.ts
        ├── domains.ts
        └── documents.ts
```

## Ownership rules

### `components/ui/`

Only shadcn generated primitives live here. Do not add product-specific business logic here.

### `components/app/`

Shared application components live here when they are not owned by a single feature. Examples: page headers, shared status badges, empty states, confirmation dialogs, and shell navigation.

### `features/<feature>/`

Feature folders own their API calls, hooks, schemas, types, and feature-specific components. This keeps backend wiring close to the UI that consumes it.

### `lib/api/`

Only generic API plumbing belongs here: the HTTP client, error normalization, auth headers, query key helpers, and shared request helpers. Do not put provider/domain/document business rules in `lib/api/`.

### `specs/<surface>/`

Every large UI surface change gets a spec folder. The spec is not permanent product documentation; it is an implementation trace that lets a junior dev or coding agent understand why the change was made.

## Naming rules

Use lowercase kebab-case filenames:

```txt
provider-config-form.tsx
provider-status-panel.tsx
domain-lifecycle-table.tsx
document-job-timeline.tsx
```

Use PascalCase exports:

```tsx
export function ProviderConfigForm() {}
export function DomainLifecycleTable() {}
```

## Import direction rules

Allowed:

```txt
app route -> feature component -> feature hook -> feature api -> lib/api/client
feature component -> components/ui
feature component -> components/app
components/app -> components/ui
```

Avoid:

```txt
components/ui -> features/*
lib/* -> features/*
feature A -> feature B internals
app route -> raw fetch directly
```

When feature A needs a visual pattern from feature B, promote the reusable part into `components/app/`.

