---
name: settings design alignment
overview: Align the client settings dialog and panels with the Ollama-inspired design direction while preserving the app's existing token-based look, dark-mode support, and settings behavior. Keep changes scoped to settings UI plus a small design-document clarification if needed.
todos:
  - id: gitnexus-impact
    content: Refresh GitNexus if needed and rerun impact analysis for settings components before editing.
    status: completed
  - id: design-md-note
    content: Clarify DESIGN.md with an app-specific settings adaptation note while preserving the Ollama-inspired direction.
    status: completed
  - id: settings-shell
    content: Restyle SettingsDialog shell, title, close button, sidebar, and route tabs to flat 12px/pill design.
    status: completed
  - id: settings-panels
    content: Restyle General, Knowledge Graph, and Account panels with local class overrides and no behavior changes.
    status: completed
  - id: validate
    content: Run lint/build and report any manual smoke-test limits.
    status: completed
isProject: false
---

# Settings Design Alignment Plan

## Direction

The current settings UI is functionally sound, but it reads more like a shadowed shadcn/ChatGPT modal than the app's stated Ollama-inspired system. I will make a settings-scoped visual pass instead of globally rewriting shared UI primitives, because changing `Button`, `Dialog`, `Input`, or `Select` would affect the whole client.

I will also make a small clarification to [DESIGN.md](DESIGN.md): keep the strict Ollama direction as the north star, but document the app-specific interpretation for production UI: use existing CSS tokens, support dark-mode equivalents, keep settings controls pill-shaped, containers at 12px, flat/no-shadow depth, and minimal grayscale-first surfaces. This matches the already implemented client better without weakening the design language.

I will use [settings.png](/data/home/tkodippili/Desktop/localTest_context_engine/settings.png) as the layout reference for the settings panel: left-side category navigation, a calm white modal, row-based settings content, subtle section dividers, generous but not sparse spacing, and lightweight inline controls. The implementation should borrow that structure and density while removing or softening anything that conflicts with `DESIGN.md`, such as strong shadows, chromatic default accents beyond focus/active control affordances, and mixed radius values.

## Targeted Changes

- Update [client/src/components/settings/SettingsDialog.tsx](client/src/components/settings/SettingsDialog.tsx) to remove the heavy modal treatment (`shadow-2xl`, `rounded-2xl`), use a 12px container radius, flatter panel surfaces, medium-weight heading, and sidebar navigation shaped like the reference image but with pill active states.
- Update [client/src/components/settings/panels/GeneralSettingsPanel.tsx](client/src/components/settings/panels/GeneralSettingsPanel.tsx) so the General tab more closely follows the reference image: a high-signal account/security card if appropriate, clean divider rows, right-aligned controls, lighter text hierarchy, and pill-shaped select triggers/switch presentation where possible through local `className` overrides.
- Update [client/src/components/settings/panels/KnowledgeGraphSettingsPanel.tsx](client/src/components/settings/panels/KnowledgeGraphSettingsPanel.tsx) so the create-domain form, inputs, refresh/action buttons, empty/loading states, and domain cards match the same flat 12px-container plus pill-control vocabulary.
- Update [client/src/components/settings/panels/AccountSettingsPanel.tsx](client/src/components/settings/panels/AccountSettingsPanel.tsx) only where needed for consistency inside the settings modal: pill buttons/selects, flatter table container, medium weights, and nested dialog class overrides if they visibly clash.

## Safety And Validation

Before implementation, I will refresh/rerun GitNexus analysis if required and run impact checks for the settings symbols. The current index did not resolve `SettingsDialog`, `GeneralSettingsPanel`, `KnowledgeGraphSettingsPanel`, or `AccountSettingsPanel`, so no reliable blast radius was available yet; expected risk is low because the planned changes are mostly `className`/layout changes and behavior remains unchanged.

For testing, I will follow the local TDD guidance proportionally: no new frontend test harness for a presentational pass. Validation will be `npm --prefix client run lint`, `npm --prefix client run build`, and a manual smoke checklist: open settings, close settings, switch General/Account/Knowledge Graph tabs, check admin and non-admin states where practical, and verify the dialog still works at narrower viewport widths.