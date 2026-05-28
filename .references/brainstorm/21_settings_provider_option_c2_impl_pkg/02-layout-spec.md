# 02 — Layout Specification

## High-level structure
The page uses three visual regions inside the existing Settings shell:

1. **Settings sidebar** (existing app shell)
2. **Provider list / summary column** (left content column)
3. **Selected provider detail pane** (right content pane)

## Content structure
### Header row
- Breadcrumb: `Settings / Provider`
- Top-right action: `Refresh status`

### Left content column
1. Section title: `Providers`
2. Subtitle: `Configure provider credentials and model profiles used by Context Engine.`
3. Provider rows
   - OpenAI
   - AWS Bedrock
   - Ollama
4. Connection health summary block
5. Last updated timestamp

### Right detail pane
1. Selected provider identity row
2. Credentials section
3. Info banner about encryption / browser non-return
4. Credential input + Save button
5. Helper text
6. Used by model profiles list
7. `Manage profiles` secondary action

## Borderless-row design grammar
This design should feel **flat, clean, low-noise**.

### Do
- Use **very soft separators** instead of heavy card borders.
- Keep panel boundaries subtle.
- Use mostly white surfaces on a light neutral canvas.
- Use one primary accent for selected row state.
- Prefer whitespace and typographic grouping over nested boxes.

### Avoid
- Heavy shadows
- Double borders
- Deep card nesting
- Too many badges competing for attention
- Excessive icon decoration

## Recommended spacing
- Page outer padding: `24px`
- Gap between left and right content panes: `24px`
- Vertical section spacing: `24px`
- Provider row vertical padding: `18–20px`
- Row content gap: `12–16px`
- Text stack gap within row: `4px`

## Recommended widths
- Left provider column: `340–380px`
- Right detail pane: fluid / remaining width
- Max content width should remain comfortable in desktop layout.

## Row anatomy
Each provider row contains:
- leading provider icon/logo
- provider name
- small metadata line (`3 profiles`, `1 profile`, `0 profiles`)
- optional status badge (`Local`) only when necessary
- trailing chevron
- selected row state indicated by a soft accent background + 2–3px accent bar on the far left

## Connection health block
Use a simple stacked list with thin dividers:
- Provider name
- Status indicator (green dot + Healthy, gray dot + No profiles, etc.)
- profile count aligned right
- small `Last updated` row below

## Detail pane anatomy
### Provider identity row
- large provider icon
- provider name
- metadata: profile count
- keep this row airy and uncluttered

### Credentials
- section heading: `Credentials`
- muted info banner beneath it
- label: `Credential`
- input field with trailing reveal / eye icon
- primary `Save key` button aligned right
- helper text below input

### Used by model profiles
- heading with count
- short helper sentence
- each profile rendered as a low-noise row with:
  - green dot
  - profile name
  - trailing chevron

## Responsive behavior
### Desktop
- 2-column content layout (provider column + detail pane)

### Tablet
- keep 2-column layout if width permits; otherwise stack with provider list above detail pane

### Mobile / narrow widths
- stack vertically
- right detail panel appears below provider list
- refresh button can move below header
