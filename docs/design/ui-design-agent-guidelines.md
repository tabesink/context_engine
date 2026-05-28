# UI Design Agent Guidelines

## Purpose

Use this document as the operating guide for coding agents that change the Context Engine frontend. The goal is not to randomly beautify screens. The goal is to preserve current product capabilities while moving presentation toward a cleaner shadcn-aligned interface with lower component entropy.

`DESIGN.md` remains the authoritative product design source. This document explains how agents should apply it during UI work.

## Non-Negotiable Principles

### Preserve Product Capability

A UI redesign must not remove existing user capabilities. Agents may change layout, grouping, visual hierarchy, copy, spacing, and component composition, but must preserve the user's ability to complete the same tasks.

For Context Engine this usually means preserving:

- Authenticated user flows.
- Admin-only controls.
- Domain selection and retrieval settings.
- Provider/API key configuration.
- LightRAG domain lifecycle visibility.
- Document upload, ingestion, processing status, and job feedback.
- Chat input, evidence return, workspace tree, source navigation, and context panel behavior.
- Error, loading, empty, disabled, and permission-denied states.

### Research Before Implementation

For meaningful UI surface changes, do not start coding until the target surface has:

- `specs/<surface>/requirements.md`
- `specs/<surface>/component-research.md`

The research file should identify candidate shadcn blocks/components, explain why they fit, list installation commands when needed, and describe implementation patterns.

Tiny visual fixes may use these rules as a lightweight checklist without creating a full spec folder unless the change grows in scope.

### Mock First When UI Shape Is Unclear

For broad layout changes, build the visual structure with local mock data first when useful. This lets the team inspect information architecture and component fit before wiring live backend data.

After the UI shape is approved, wire existing API contracts through the current frontend boundaries.

### Keep shadcn Defaults Unless There Is a Product Reason to Override

Use shadcn's default grammar as the baseline: neutral surfaces, readable spacing, clear labels, consistent variants, restrained borders, and accessible contrast.

Do not introduce one-off colors, shadow systems, or bespoke component variants unless they are added through shared tokens and documented in `DESIGN.md` or a linked design doc.

### Low Entropy Over Novelty

Prefer fewer composable primitives over many custom components. If a pattern repeats across screens, extract it into `client/src/components/surfaces/` or another existing shared area only after at least two real surfaces need it.

### Verification Is Part of Design

The first implementation is not complete until the changed UI has been inspected through Playwright/screenshots or equivalent visual verification and checked against requirements.

Some design problems, such as poor contrast or confusing button states, are hard for a coding agent to infer without seeing the UI.

## Workflow Gates

For every meaningful UI surface change, produce or update:

```txt
specs/<surface>/requirements.md
specs/<surface>/component-research.md
specs/<surface>/implementation-plan.md
specs/<surface>/verification-report.md
```

Implementation may proceed only after `requirements.md` and `component-research.md` exist.

## UI Quality Bar

Every changed surface must include, where applicable:

- Clear page title and short helper text.
- Obvious primary action.
- Grouped secondary actions.
- Empty, loading, success, warning, error, disabled, and permission-denied states.
- Mobile/tablet/desktop responsive behavior.
- Keyboard-accessible controls.
- No hidden admin-only controls for non-admin users.
- No duplicate lifecycle verbs unless the backend explicitly requires them.
- No confusing disabled states that look like broken controls.
- No visual state that depends on color alone.

## Context Engine Design Language

Use a restrained application-console style rather than a marketing-site style.

Recommended visual direction:

- shadcn-native neutral base.
- Subtle accent usage for state, selection, and primary action.
- Compact but breathable cards.
- Light borders instead of heavy shadows.
- Clear hierarchy using size, weight, and spacing rather than loud color.
- Left navigation for major app areas.
- Right contextual panel for evidence/context/source navigation when used by chat or workspace flows.
- Tables for dense admin lists; cards for object summaries and decision surfaces.

## Recommended Component Grammar

Use these patterns consistently:

- `Card` for grouped object summary and settings sections.
- `Tabs` for switching between related views without navigation.
- `Table` for dense administrative data.
- `Badge` for state/status.
- `Button` variants for action hierarchy.
- `DropdownMenu` for secondary row actions.
- `Dialog` or inline confirmation panel for destructive actions.
- `Sheet` only for temporary side inspection, not primary persistent configuration.
- `Tooltip` for compact icon-only controls.
- `Skeleton` for loading placeholders.
- `Alert` for warnings and irreversible actions.

## Anti-Patterns

Avoid:

- Building from screenshots alone without listing retained capabilities.
- Installing random component registries without documenting why.
- Copy-pasting large blocks without adapting data flow, accessibility, and states.
- One-off CSS classes that conflict with `DESIGN.md` tokens.
- Hiding required state behind hover-only interactions.
- Showing admin actions to normal users and relying on backend rejection only.
- Treating Playwright verification as optional for meaningful UI surface changes.
- Redesigning API contracts as part of a visual refactor.
