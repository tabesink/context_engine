# Coding Agent Handoff: Design-Guided UI Implementation

## Role

You are a senior frontend coding agent working on Context Engine. Your job is to redesign UI surfaces using shadcn-style components while preserving current product capabilities, backend contracts, and role-based behavior.

## Required Procedure

For each meaningful UI surface change:

1. Create or update `specs/<surface>/requirements.md`.
2. Create or update `specs/<surface>/component-research.md` using shadcn/MCP or registry research.
3. Create or update `specs/<surface>/implementation-plan.md`.
4. Implement the smallest complete vertical slice.
5. Run Playwright, screenshot, or equivalent visual verification.
6. Create or update `specs/<surface>/verification-report.md`.
7. Fix issues found during verification.

For tiny visual fixes, apply the same design principles as a checklist and escalate to the full workflow if the change affects a full surface, introduces new component composition, or changes user-visible behavior.

## Do Not Skip These Steps

Do not code meaningful UI surface changes before requirements and component research are written.

Do not remove existing capability unless explicitly listed as a removal in the requirements file.

Do not create new API contracts when existing endpoints can support the UI.

Do not hide important persistent settings in temporary overlays if the design direction calls for inline panels.

## Surface Checklist

Before committing or handing off, confirm:

- Existing user capabilities remain available.
- Admin-only actions remain admin-only.
- Loading, error, empty, and success states exist where applicable.
- Destructive actions require confirmation.
- Status labels are clear and not color-only.
- The UI follows `DESIGN.md` tokens and shadcn grammar.
- The page works with live API data or clearly isolated mock fixtures.
- Tests or visual verification cover the changed surface.

## Recommended First Surfaces

1. Providers settings route.
2. Domain lifecycle/admin route.
3. Documents and document processing status route.
4. Chat composer and right-side context/source navigation panel.

## API Wiring Guidance

Use existing frontend boundaries:

```txt
client/src/api/
client/src/lib/api/
client/src/hooks/
client/src/stores/
client/src/types/
```

Keep the shared client and generic helpers focused on transport, error normalization, auth headers, and request helpers. Do not turn shared API modules into dumping grounds for provider/domain/document business rules.

## Component Placement Guidance

```txt
client/src/components/ui/          shadcn primitives only
client/src/components/surfaces/    reused surface primitives
client/src/components/settings/    settings and admin surfaces
client/src/components/chat/        chat, retrieval, context/source surfaces
client/src/components/graph/       graph visualization surfaces
```

Promote reusable presentation pieces only after two or more real surfaces need them.
