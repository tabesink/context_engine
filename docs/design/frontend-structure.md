# Frontend Structure For UI Agents

This document adapts the design-agent package's folder guidance to Context Engine's current frontend layout. Do not force a feature-folder migration as part of ordinary UI work.

## Repository-Level Structure

```txt
context_engine/
├── client/                         # Next.js frontend
│   ├── components.json             # shadcn configuration
│   └── src/
│       ├── app/                    # Next.js routes
│       ├── components/             # UI, surface, settings, chat, graph components
│       ├── api/                    # Frontend API functions for app-owned endpoints
│       ├── lib/                    # Cross-cutting frontend utilities and API clients
│       ├── hooks/                  # Shared frontend hooks
│       ├── stores/                 # Zustand/client state boundaries
│       └── types/                  # Shared frontend types
├── docs/
│   ├── design/                     # Product-wide design docs
│   └── agent-workflows/            # Coding-agent workflows and handoffs
├── specs/                          # Per-surface implementation traces
└── .cursor/
    ├── rules/                      # Cursor/coding-agent rules
    └── agents/                     # Reusable agent prompts
```

## Current Frontend Boundaries

```txt
client/src/
├── app/
│   ├── chat/
│   ├── database-visualize/
│   ├── settings/
│   └── page.tsx
├── components/
│   ├── ui/                         # shadcn generated primitives only
│   ├── surfaces/                   # shared Context Engine surface primitives
│   ├── settings/                   # settings dialog and settings sub-surfaces
│   ├── chat/                       # chat, workspace tree, context/source panels
│   ├── graph/                      # graph visualization components
│   ├── icons/
│   └── layout/
├── api/                            # app-level frontend API modules
├── lib/
│   ├── api/                        # generic/surface API client modules
│   └── ...
├── hooks/
├── stores/
└── types/
```

## Ownership Rules

### `client/src/components/ui/`

Only shadcn generated primitives live here. Do not add product-specific business logic here.

### `client/src/components/surfaces/`

Shared application surface primitives live here when they are reused across at least two real surfaces. Examples include section cards, status chips, surface headers, and panel state components.

### Surface Component Folders

Feature-specific UI should stay near the surface that owns it:

- Settings and admin UI: `client/src/components/settings/`
- Chat and retrieval UI: `client/src/components/chat/`
- Graph UI: `client/src/components/graph/`

Do not move a component into a new feature architecture unless the user explicitly asks for that refactor.

### API, Hooks, Stores, And Types

Use the current frontend boundaries:

- `client/src/api/` for app-level endpoint modules already following that pattern.
- `client/src/lib/api/` for API clients and admin/service-specific API helpers already following that pattern.
- `client/src/hooks/` for reusable hooks.
- `client/src/stores/` for client state boundaries.
- `client/src/types/` for shared frontend type definitions.

Avoid raw fetch calls directly in route components when a local API module or hook should own the contract.

## Naming Rules

Use lowercase kebab-case filenames for new component files:

```txt
provider-config-form.tsx
domain-lifecycle-table.tsx
document-job-timeline.tsx
```

Use PascalCase exports:

```tsx
export function ProviderConfigForm() {}
export function DomainLifecycleTable() {}
```

Existing files may use older naming conventions. Do not rename them unless the user explicitly asks for a refactor.

## Import Direction Rules

Allowed:

```txt
route -> surface component -> hook/api module -> API client
surface component -> components/ui
surface component -> components/surfaces
components/surfaces -> components/ui
```

Avoid:

```txt
components/ui -> settings/chat/graph components
lib/* -> surface component internals
surface A -> surface B internals
route -> raw fetch directly
```

When one surface needs a visual pattern from another, promote the reusable part into `client/src/components/surfaces/` after it has proven reuse.

## Existing Design Tension

`DESIGN.md` describes `style: default` as the preferred shadcn direction, while `client/components.json` currently uses `style: new-york`. Treat `client/components.json` as the current app fact unless a separate design-system migration explicitly changes it.
