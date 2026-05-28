# Coding Agent Handoff: Design-Guided UI Implementation

## Role

You are a senior frontend coding agent working on Context Engine. Your job is to redesign UI surfaces using shadcn-style components while preserving the product’s current capabilities, backend contracts, and role-based behavior.

## Required procedure

For each requested UI surface:

1. Create `specs/<surface>/requirements.md`.
2. Create `specs/<surface>/component-research.md` using shadcn/MCP research.
3. Create `specs/<surface>/implementation-plan.md`.
4. Implement the smallest complete vertical slice.
5. Run Playwright/visual verification.
6. Create `specs/<surface>/verification-report.md`.
7. Fix issues found during verification.

## Do not skip these steps

Do not code before requirements and component research are written.

Do not remove existing capability unless explicitly listed as a removal in the requirements file.

Do not create new API contracts when existing endpoints can support the UI.

Do not hide important persistent settings in temporary overlays if the design direction calls for inline panels.

## Surface checklist

Before committing, confirm:

- Existing user capabilities remain available.
- Admin-only actions remain admin-only.
- Loading, error, empty, and success states exist.
- Destructive actions require confirmation.
- Status labels are clear and not colour-only.
- The UI follows existing `design.md` tokens and shadcn grammar.
- The page works with live API data or clearly isolated mock fixtures.
- Tests or Playwright verification cover the changed surface.

## Recommended first surfaces

1. Providers settings route.
2. Domain lifecycle/admin route.
3. Documents and document processing status route.
4. Chat composer and right-side context/source navigation panel.

## API wiring guidance

Use feature-local API modules:

```txt
features/providers/api.ts
features/providers/hooks.ts
features/providers/types.ts
features/domains/api.ts
features/domains/hooks.ts
features/documents/api.ts
features/documents/hooks.ts
features/chat/api.ts
features/chat/hooks.ts
```

Use the shared client only for transport:

```txt
lib/api/client.ts
lib/api/errors.ts
lib/api/query-keys.ts
```

This keeps the frontend lean and prevents a single large API utility file from becoming a dumping ground.

