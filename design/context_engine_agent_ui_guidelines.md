# Context Engine Agent UI Guidelines

This guide recreates the visual language from the supplied reference images and applies it to Context Engine coding-agent surfaces.

## Core visual direction

- White canvas first. Avoid heavy cards, sidebars, and decorative frames.
- Use faint dotted workbench backgrounds only where a queue/workflow screen benefits from spatial orientation.
- Prefer md-rounded controls, not pill controls.
- Use compact, developer-native typography.
- Represent state with tiny dots, checkmarks, muted badges, and progress bars.
- Keep color minimal and semantic: green for done/success, blue for running/current, orange for paused/high priority, red only for risk.

## Radius system

| Element | Radius |
|---|---:|
| Buttons | 8px |
| Inputs / selects | 8px |
| Chips / badges | 8px |
| Active rows | 8px |
| Floating toolbar segments | 8px |
| Panels / preview frames | 12px |

Do not use 9999px full-pill controls for this direction.

## Typography

- UI labels: 13–14px sans-serif.
- Metadata: 10–12px monospace.
- Section titles: 15–22px medium weight.
- Code panes and paths: monospace.
- Avoid bold-heavy headings. Use spacing and position for hierarchy.

## Component grammar

Use these components repeatedly:

1. Execution plan step rail
2. Task queue table
3. API playground split pane
4. Agent workflow pipeline columns
5. Small status badges
6. Tiny semantic dots
7. Faint progress tracks
8. Floating bottom configuration toolbar

## Implementation notes for coding agent

- Use Tailwind/shadcn primitives, but override default large rounding when needed.
- Map controls to `rounded-md`, not `rounded-full`.
- Use `border border-neutral-200`, `bg-white`, `bg-neutral-50`, and `text-neutral-*`.
- Keep shadows off except the floating bottom toolbar, which may use a very soft shadow.
- Do not use saturated brand panels or colorful cards.
