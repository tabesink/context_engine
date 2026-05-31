# Coding Agent Prompt — Apply Flat Graphite Context Engine Design System

You are a senior frontend engineer working in `context_engine/client`. Your goal is to apply the updated flat graphite design system without changing backend behavior.

## Inputs

- Read `DESIGN.md` first.
- Use `GRAPHITE_ACCENT_TOKENS.css` as the token reference.
- Use `UI_COMPONENT_INVENTORY.md` to understand the existing WebUI surfaces.
- Use the standalone browser preview package to compare accent themes before touching production components.

## Hard constraints

- Do not add a second UI framework.
- Keep shadcn-style local primitives in `client/src/components/ui`.
- Keep Tailwind CSS variable token approach.
- Do not make backend/API changes for this task.
- Do not add gradients, heavy shadows, glassmorphism, or colorful AI decoration.
- Do not turn every row into a card.
- Preserve admin-only behavior and existing auth/session flows.

## Implementation goals

1. Add graphite + accent tokens to `globals.css` or a token file consumed by `globals.css`.
2. Update core primitives only where needed:
   - Button: pill radius for normal buttons, quiet variants, no default shadow.
   - Badge: muted/default variants, selected accent variant.
   - Card: no shadow, 12px radius, thin border.
   - Input/Select: low-contrast border, focus ring, pill for short fields.
3. Add product primitives:
   - `SettingsRow`
   - `DisclosureRow`
   - `FlatRadioGroup`
   - `CitationMap`
   - `EvidenceCard`
   - `StatusRow`
   - `ObjectList`
4. Flatten settings and domain creation forms:
   - remove nested fieldset/card borders unless necessary
   - use labels, helper text, spacing, and dividers
   - keep input/select control affordances
5. Keep evidence panel prominent:
   - compact citation map
   - evidence cards with document-first metadata
   - image/table evidence variants
6. Keep workspace tree file-explorer-like:
   - no carded tree rows
   - selected row uses accent-soft + left rail/dot

## Acceptance criteria

- The app still builds.
- Login/session routing is unchanged.
- Chat composer still submits retrieval requests.
- Domain selection remains clear.
- Settings are flatter and have fewer internal boundaries.
- Evidence panel is more scannable.
- The selected accent theme is implemented with tokens only.
- No raw accent hex values are scattered across components.
