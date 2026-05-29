# Context Engine UI Design System

This document is the source of truth for Context Engine application UI. It replaces the older Ollama-style reference with a direction built specifically for coding-agent workflows: quiet, compact, white-canvas interfaces that make plans, queues, execution state, API calls, and agent progress easy to scan.

When implementing UI, also consult `design/context_engine_agent_ui_guidelines.md` for the concise agent-facing checklist.

## 1. Visual Direction

Context Engine should feel like a precise developer workbench, not a marketing page and not a heavy admin dashboard. The baseline is a white canvas with restrained borders, compact typography, and state expressed through small, semantic cues.

Core characteristics:

- White canvas first. Avoid heavy cards, saturated panels, decorative frames, and visual noise.
- Use faint dotted workbench backgrounds only when a queue, plan, canvas, or workflow screen benefits from spatial orientation.
- Prefer `rounded-md` controls. Do not use full-pill controls as the default visual language.
- Use compact, developer-native typography with monospace for paths, metadata, IDs, timing, code, and API details.
- Represent state with tiny dots, checkmarks, muted badges, narrow progress bars, and concise labels.
- Keep color minimal and semantic: green for done/success, blue for running/current, orange for paused or high-priority attention, and red only for risk or failure.

The interface should stay calm even when the system is busy. Let information density come from layout and typography, not from color, shadows, or large components.

## 2. Color System

### Foundation

- **Page background**: `bg-white`
- **Subtle surface**: `bg-neutral-50`
- **Raised surface**: `bg-white`
- **Primary text**: `text-neutral-950`
- **Secondary text**: `text-neutral-600`
- **Muted text**: `text-neutral-500`
- **Disabled text**: `text-neutral-400`
- **Primary border**: `border-neutral-200`
- **Subtle divider**: `border-neutral-100`
- **Focus ring**: Tailwind blue focus ring or the existing app token equivalent

### Semantic State

Use semantic color sparingly and locally:

- **Running / current**: blue dot, blue text accent, or narrow blue progress fill
- **Done / success**: green dot, checkmark, or muted green badge
- **Paused / queued / priority**: orange dot or badge
- **Risk / error**: red dot, error text, or compact destructive badge
- **Idle / inactive**: neutral dot, neutral badge, or muted text

Avoid saturated color blocks. Semantic color should usually appear as a dot, icon, border accent, badge text, or progress fill rather than as a full panel background.

## 3. Radius System

Use a small, predictable radius scale:

| Element | Radius |
| --- | ---: |
| Buttons | 8px |
| Inputs / selects | 8px |
| Chips / badges | 8px |
| Active rows | 8px |
| Floating toolbar segments | 8px |
| Panels / preview frames | 12px |

Implementation guidance:

- Map most controls to Tailwind `rounded-md`.
- Use `rounded-lg` for panels, preview frames, and larger grouped containers.
- Do not use `rounded-full` / `9999px` controls unless there is a specific existing component requirement.
- Avoid mixing many radius values in one view.

## 4. Button Sizing

Buttons should be compact and consistent within each surface.

| Button Type | Size |
| --- | ---: |
| Standard text action | 32px height, 12px horizontal padding |
| Primary text action | 32px height, 12px horizontal padding |
| Icon-only action | 32px square |

Implementation guidance:

- Prefer shadcn `Button` with `size="sm"` for text actions inside app panels.
- Prefer shadcn `Button` with `size="icon-sm"` for icon-only actions.
- Keep primary, secondary, and destructive buttons the same height when they appear in one action group.
- Use longer labels only when necessary; do not compensate with taller buttons.

## 5. Typography

The type system should feel compact and native to developer tools.

| Role | Size | Weight | Font | Notes |
| --- | ---: | ---: | --- | --- |
| Page title | 20-22px | 500-600 | Sans | Short, direct labels |
| Section title | 15-18px | 500 | Sans | Avoid bold-heavy hierarchy |
| UI label | 13-14px | 400-500 | Sans | Buttons, tabs, form labels |
| Body text | 13-15px | 400 | Sans | Explanations and row content |
| Metadata | 10-12px | 400-500 | Monospace | IDs, paths, durations, tokens |
| Code / API | 12-14px | 400 | Monospace | Requests, snippets, traces |

Principles:

- Use spacing and position for hierarchy before increasing size or weight.
- Keep headings restrained. Avoid oversized marketing-style display type inside app surfaces.
- Use monospace deliberately for developer meaning: file paths, run IDs, API routes, model names, symbols, timestamps, and code.
- Avoid all-caps labels except for very small metadata when the existing component style already uses it.

## 6. Component Grammar

These components should appear repeatedly across the app so agent workflows feel consistent.

### Execution Plan Step Rail

Use for plans, multi-step runs, evaluations, and agent tasks.

- Left rail with tiny status dots or checkmarks.
- Current step uses blue state; completed steps use green checks; blocked steps use red risk markers.
- Step content stays compact: title, one-line summary, optional metadata row.
- Avoid large timeline cards unless the content truly needs expanded detail.

### Task Queue Table

Use for pending work, background jobs, batch ingestion, syncs, and evaluation runs.

- Table rows on white with subtle dividers.
- Active or selected row may use `bg-neutral-50` and `rounded-md`.
- State appears as a tiny dot plus short text badge.
- Primary row text should be readable at a glance; metadata should be small and muted.

### API Playground Split Pane

Use for request/response, context inspection, prompt testing, and integration flows.

- Two-pane layout: controls/request on one side, output/preview on the other.
- Code and payload areas use monospace and subtle bordered containers.
- Keep panels white or neutral-50 with `border-neutral-200`.
- Prefer compact controls and inline configuration over tall forms.

### Agent Workflow Pipeline Columns

Use for multi-agent or staged work: planned, queued, running, reviewing, done.

- Columns should be light and quiet, not kanban-heavy.
- Cards remain compact with minimal borders and state dots.
- Use dotted workbench backgrounds only if it helps the pipeline read as a workspace.
- Keep per-card actions secondary until hover/focus when possible.

### Small Status Badges

Use badges for machine-readable state, model/provider labels, risk levels, and environment names.

- Badge radius: `rounded-md`.
- Prefer neutral badges with semantic dot or text color.
- Keep labels short: `running`, `done`, `blocked`, `high`, `local`, `prod`.
- Avoid large colorful pills.

### Tiny Semantic Dots

Use dots where a full badge would be too loud.

- 6-8px is usually enough.
- Pair with text for accessibility unless the surrounding label is unambiguous.
- Use dots consistently across tables, rails, and headers.

### Faint Progress Tracks

Use progress tracks for execution, indexing, ingestion, test runs, and batch jobs.

- Height should be slim, usually 3-6px.
- Track uses neutral-100 or neutral-200.
- Fill uses semantic color only for current state.
- Prefer exact labels nearby for longer operations.

### Quiet Underline Inputs

Use for compact credential fields, inline settings values, and low-chrome configuration rows where a full bordered input would add too much visual weight.

- Field uses a subtle gray fill, usually `bg-neutral-50`, with no full box border.
- Structure comes from a clean bottom border only, usually `border-b border-neutral-300`.
- On focus, keep the underline calm and visible, such as `focus-visible:border-neutral-500`, without adding a heavy ring.
- Keep the control compact: 32px height, `rounded-none` or only inherited container rounding, and quiet placeholder text.
- Use a normal bordered `rounded-md` input instead when the field appears alone, needs strong affordance, or sits on a gray panel where the underline would lose contrast.

### Floating Bottom Configuration Toolbar

Use for persistent run configuration, selected context, model/provider controls, or staged actions.

- It may use the only soft shadow in the system.
- Keep segments `rounded-md` with subtle borders.
- Avoid making it look like a marketing CTA bar.
- It should feel like a compact tool tray.

## 7. Layout Principles

### Density

Context Engine is a work app. It can be information-dense, but each view needs a clear scan path.

- Put the primary workflow in the center, not inside nested decorative panels.
- Use side panels for context, settings, previews, or traces.
- Keep rows compact, but preserve enough vertical rhythm to avoid spreadsheet fatigue.
- Favor progressive disclosure for logs, traces, and advanced controls.
- Place row or container action groups on the right-hand side of the container. In left-to-right layouts, keep primary content and metadata on the left, while lifecycle/destructive actions align right.

### Spacing

- Base unit: 4px or 8px depending on the existing component scale.
- Common gaps: 4px, 8px, 12px, 16px, 24px, 32px.
- Controls should feel compact, not cramped.
- Dense tables and rails should rely on dividers and whitespace instead of card shadows.
- Keep repeated settings sections on a predictable rhythm:
  - 16px between top-level sections.
  - 12px between a section heading and its panel, table, or row group.
  - 16px panel padding for standard settings panels.
  - 16px between form field groups.
  - 6px between a field label/help line and its control.
  - 8px between related action buttons.
- Do not use one-off padding nudges like `pt-1` to align section headings; group the heading and content with spacing utilities instead.

### Containers

- Use borders and subtle background shifts for separation.
- Default panels: `bg-white border border-neutral-200 rounded-lg`.
- Secondary areas: `bg-neutral-50 border border-neutral-200 rounded-lg`.
- Avoid nested card stacks. If a panel contains rows, use dividers instead of placing each row in a card.

## 8. Depth And Motion

Depth should be nearly flat.

- Most surfaces use no shadow.
- The floating bottom toolbar may use a very soft shadow.
- Use one-pixel borders and neutral background changes for structure.
- Motion should be brief and functional: loading progress, row insertion, disclosure open/close.
- Avoid decorative animation, bouncy easing, and dramatic hover effects.

## 9. Implementation Notes

When coding UI:

- Prefer existing Tailwind and shadcn primitives.
- Override default large rounding when needed: `rounded-md` for controls, `rounded-lg` for panels.
- Use `border border-neutral-200`, `bg-white`, `bg-neutral-50`, and `text-neutral-*` as defaults.
- For quiet credential or inline settings fields, use gray-fill underline inputs: `bg-neutral-50`, no full border, `border-b border-neutral-300`, and a restrained focus underline.
- Keep shadows off except for the floating bottom toolbar.
- Do not introduce saturated brand panels, colorful cards, gradients, or default pill-heavy styling.
- Make state legible with text, not color alone.
- Preserve keyboard focus styling and accessible labels.
- Keep empty, loading, and error states visually consistent with the same compact grammar.

## 10. Do And Do Not

### Do

- Use a white canvas and subtle neutral surfaces.
- Use `rounded-md` controls and `rounded-lg` panels.
- Use small semantic dots, checkmarks, muted badges, and slim progress bars.
- Use monospace for paths, symbols, code, IDs, and timing.
- Build views around execution plans, task queues, API panes, and workflow columns.
- Keep shadows, color, and ornament restrained.

### Do Not

- Do not default to full-pill buttons, badges, tabs, or inputs.
- Do not use saturated cards, brand-color panels, or decorative gradients.
- Do not create heavy dashboard chrome around every screen.
- Do not use red for normal urgency; reserve red for risk, destructive actions, and failure.
- Do not rely on color alone to communicate state.
- Do not add decorative illustrations unless the product surface specifically calls for an empty-state visual.

## 11. Agent Prompt Guide

Use these prompts when asking an agent to implement or revise UI:

- "Build this as a compact Context Engine workbench screen on a white canvas. Use `rounded-md` controls, `rounded-lg` panels, neutral borders, and semantic micro-status dots."
- "Create an execution plan rail with compact steps, tiny state markers, muted metadata, and a blue current step. Completed steps should use green checkmarks."
- "Design a task queue table with subtle row dividers, neutral badges, tiny semantic dots, and compact monospace metadata for IDs and durations."
- "Create an API playground split pane with a request/config panel and a response/code preview panel. Use white and neutral-50 surfaces, 1px neutral borders, and monospace code areas."
- "Add a floating bottom configuration toolbar with segmented `rounded-md` controls, a soft shadow, neutral borders, and compact run settings."

Before accepting UI work, verify:

1. Controls are `rounded-md`, not full-pill by default.
2. Panels are quiet, white or neutral-50, and lightly bordered.
3. State is visible through small semantic markers plus text.
4. Typography is compact and developer-native.
5. Shadows, gradients, saturated colors, and decorative cards have been removed unless explicitly justified.
