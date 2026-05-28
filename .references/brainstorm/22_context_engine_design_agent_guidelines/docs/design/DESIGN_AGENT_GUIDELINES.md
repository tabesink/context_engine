# Design Agent Guidelines for Context Engine UI

## Purpose

Use this document as the operating guide for a coding agent that is changing the Context Engine frontend. The goal is not to randomly beautify screens. The goal is to preserve the current product capabilities while changing the presentation layer to a cleaner, shadcn-aligned interface with lower component entropy.

The transcript describes a repeatable UI agent workflow:

1. Set up and verify the shadcn MCP/server tooling.
2. Analyze requirements, acceptance criteria, and target features.
3. Research shadcn components/blocks and registries before coding.
4. Implement from the requirements and research documents.
5. Use Playwright/screenshot-based verification to catch visual and UX issues.

## Non-negotiable principles

### 1. Preserve product capability

A UI redesign must not remove existing user capabilities. The agent may change layout, grouping, visual hierarchy, copy, spacing, and component composition, but must preserve the user’s ability to complete the same tasks.

For Context Engine this usually means preserving:

- Authenticated user flows.
- Admin-only controls.
- Domain selection and retrieval settings.
- Provider/API key configuration.
- LightRAG domain lifecycle visibility.
- Document upload, ingestion, processing status, and job feedback.
- Chat input, evidence return, workspace tree, source navigation, and context panel behavior.
- Error, loading, empty, disabled, and permission-denied states.

### 2. Research before implementation

Do not start coding until the component research file exists for the target surface. The research file should identify candidate shadcn blocks/components, explain why they fit, list installation commands, and describe implementation patterns.

### 3. Mock-first, API-second for UI shape changes

For broad layout changes, build the visual structure with local mock data first when useful. This allows the team to inspect information architecture and component fit before wiring to live backend data. After the UI shape is approved, wire the existing API contracts with thin feature-level hooks.

### 4. Keep shadcn defaults unless there is a product reason to override

Use shadcn’s default grammar as the baseline: neutral surfaces, readable spacing, clear labels, consistent variants, restrained borders, and accessible contrast. Do not introduce one-off colours, shadow systems, or bespoke component variants unless they are added through shared tokens and documented.

### 5. Low entropy over novelty

Prefer fewer composable primitives over many custom components. If a pattern repeats across screens, extract it into `components/app/` or a feature-local component depending on ownership.

### 6. Verification is part of the design process

The first implementation is not complete until the UI has been inspected through Playwright/screenshots and checked against requirements. The transcript specifically highlights that some design problems, such as poor colour contrast or confusing button states, are hard for a coding agent to infer without seeing the UI.

## Agent workflow gates

A coding agent must produce these files for every meaningful UI surface change:

```txt
specs/<surface>/requirements.md
specs/<surface>/component-research.md
specs/<surface>/implementation-plan.md
specs/<surface>/verification-report.md
```

The implementation may proceed only after `requirements.md` and `component-research.md` exist.

## UI quality bar

Every changed surface must include:

- Clear page title and short helper text.
- Obvious primary action.
- Grouped secondary actions.
- Empty, loading, success, warning, and error states.
- Mobile/tablet/desktop responsive behavior where applicable.
- Keyboard-accessible controls.
- No hidden admin-only controls for non-admin users.
- No duplicate lifecycle verbs unless the backend explicitly requires them.
- No confusing disabled states that look like broken controls.
- No visual state that depends on colour alone.

## Design language for Context Engine

Use a restrained application-console style rather than a marketing-site style.

Recommended visual direction:

- Neutral graphite/stone base.
- Subtle accent usage for state, selection, and primary action.
- Compact but breathable cards.
- Light borders instead of heavy shadows.
- Clear hierarchy using size, weight, and spacing rather than loud colour.
- Left navigation for major app areas.
- Right contextual panel for evidence/context/source navigation when used by chat or workspace flows.
- Tables for dense admin lists; cards for object summaries and decision surfaces.

## Recommended component grammar

Use these patterns consistently:

- `Card` for grouped object summary and settings sections.
- `Tabs` for switching between related views without navigation.
- `Table` for dense administrative data.
- `Badge` for state/status.
- `Button` variants for action hierarchy.
- `DropdownMenu` for secondary row actions.
- `Dialog` or inline confirmation panel for destructive actions.
- `Sheet` only when the user’s intent is temporary side inspection; avoid using sheets for major persistent forms when the product decision says forms should remain on-page.
- `Tooltip` for compact icon-only controls.
- `Skeleton` for loading placeholders.
- `Alert` for warnings and irreversible actions.

## Anti-patterns

Avoid:

- Building from screenshots alone without listing retained capabilities.
- Installing random component registries without documenting why.
- Copy-pasting large blocks without adapting data flow, accessibility, and states.
- One-off CSS classes that conflict with `design.md` tokens.
- Hiding required state behind hover-only interactions.
- Showing admin actions to normal users and relying on backend rejection only.
- Treating Playwright verification as optional.
- Redesigning API contracts as part of a visual refactor.

