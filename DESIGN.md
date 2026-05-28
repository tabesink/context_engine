# Context Engine DESIGN.md — shadcn Theme Alignment Update

## Design Direction

Context Engine should retain its low-entropy, technical, workspace-first interface while allowing the default visual language of shadcn/ui blocks to come through. The app should no longer be described as strictly flat grayscale only. Instead, the baseline should be:

- shadcn default theme tokens first
- restrained neutral base color
- subtle semantic color accents
- compact technical UI density
- low visual noise
- no decorative gradients or heavy marketing polish
- wholesale shadcn block imports are allowed and preferred when they improve professional UI quality

The goal is to make Context Engine feel like a clean shadcn-native application, not a custom grayscale shell fighting against shadcn defaults.

## Theme Foundation

Use shadcn/ui CSS variables as the design-system source of truth.

Preferred configuration:

```json
{
  "style": "default",
  "tailwind": {
    "baseColor": "neutral",
    "cssVariables": true
  }
}
```

Acceptable base colors:

- `neutral` — preferred default; clean, technical, balanced
- `zinc` — acceptable if the UI needs slightly cooler contrast
- `slate` — acceptable for more blue-gray system surfaces

Avoid defining many custom one-off colors in components. Use semantic tokens such as:

- `background`
- `foreground`
- `card`
- `card-foreground`
- `muted`
- `muted-foreground`
- `border`
- `input`
- `primary`
- `secondary`
- `accent`
- `destructive`
- `ring`
- `sidebar`

## Color Philosophy

The UI should use shadcn’s default neutral color system as the foundation, with small semantic accents only where they communicate state or hierarchy.

Use color for:

- active selected route
- selected domain
- active lifecycle state
- processing / queued / failed / indexed status
- destructive warnings
- focused inputs
- primary actions
- subtle charts or counters when useful

Do not use color for:

- decorative card backgrounds
- arbitrary section branding
- random icons
- every badge in a list
- large gradient panels
- dense rainbow dashboards

## Recommended Semantic Status Colors

Use existing shadcn semantic tokens where possible.

Suggested mapping:

| State | Visual Treatment |
|---|---|
| Ready / indexed / healthy | subtle success chip, restrained green or default primary only if success tokens exist |
| Queued / pending | muted chip |
| Processing / scanning | accent or primary outline chip |
| Warning / stale | warning token if added globally; otherwise muted amber utility with restraint |
| Failed / unhealthy | destructive token |
| Archived / stopped | secondary or muted chip |
| Purging / destructive operation | destructive outline or destructive filled confirmation state |

If warning/success tokens are needed, add them globally as CSS variables rather than hardcoding colors in individual components.

## Layout and Component Grammar

Prefer importing shadcn blocks wholesale as the default approach, then make only minimal Context Engine-specific adjustments.

Use:

- compact cards
- quiet borders
- semantic badges
- tabs for mode switching
- data tables for registries
- alert/banner rows for active processing
- timeline/activity rows for lifecycle events
- dialogs/sheets for advanced or destructive operations
- skeletons for loading states
- empty states for no domains, no documents, no jobs, or no source selected

Avoid:

- oversized hero sections
- landing-page CTA blocks
- decorative glassmorphism
- heavy drop shadows
- unnecessary charts
- duplicate cards that repeat the same status in different words
- showing every backend operation as a primary button

## Radius and Shape

Use the shadcn radius scale rather than custom ad hoc radii. Settings and admin surfaces follow **Option C2 subtle rounding** (~6–8px), not pill-shaped controls.

Guidance:

- **`rounded-md`** — default for buttons, inputs, selects, textareas, and compact settings controls (maps to `--radius-md`, ~6px when `--radius: 0.5rem`)
- **`rounded-lg`** — row groups, profile lists, bordered list containers with internal dividers
- **`rounded-xl`** — dialog shell, sparing card/panel chrome; prefer borderless settings rows over nested boxed cards
- **`rounded-full`** — reserved for status dots, avatars, progress tracks, switch thumbs, and tiny circular affordances only — **not** standard settings buttons or inputs
- Avoid mixing many radius styles on one surface

Do not override shadcn `Button` / `Input` defaults with `rounded-full` in settings panels. Use shared tokens in `client/src/components/settings/settings-controls.ts` when local class overrides are needed.

The global `--radius` token in `client/src/app/globals.css` is the source of truth; let components scale consistently from it.

### Settings Provider (Option C2)

The **Settings → Provider** route is the reference implementation for flat, low-noise admin settings:

- Three regions: settings sidebar | provider list column (~360px) | selected-provider detail pane
- Leading provider brand icon (OpenAI, AWS, Ollama) in list rows and detail header
- Selected row: soft accent background + 2–3px left accent bar; avoid heavy nested card borders
- Connection health: thin dividers, status dots, profile counts — not noisy cards
- Credentials: lock/info banner, `rounded-md` input with reveal toggle, primary Save action
- Model profiles: grouped `rounded-lg` container, green status dot, model name only, trailing chevron

## Shadows and Elevation

Default stance: avoid decorative shadows.

Allowed:

- very subtle native shadcn shadow only if the imported block relies on it for separation
- focus rings
- popover/dialog/sheet elevation where needed for layering

Avoid:

- stacked shadow cards
- glossy panels
- heavy dashboard depth
- animated glow or gradient shadow effects

## Typography

Keep typography restrained and technical.

Use:

- clear section titles
- small supporting descriptions
- tabular numbers for metrics when useful
- compact metadata labels
- uppercase micro-labels only sparingly

Avoid:

- marketing-style oversized headings inside the app shell
- excessive font weights
- dense all-caps labels

## Recommended shadcn Block Patterns for Context Engine

Use shadcn blocks as direct implementation baselines. Preserve block visual quality unless a concrete product constraint requires adaptation.

### Admin LightRAG Domain Lifecycle

Use dashboard, monitoring, workflow, settings, and danger-zone block patterns.

Recommended composition:

- domain health overview
- domain registry table
- selected-domain runtime card
- lifecycle workflow card
- processing queue card
- recent lifecycle events
- danger zone for archive/purge

### Document Processing Status

Use processing dashboard, job queue, table, badge, and timeline patterns.

Show:

- per-document status
- current stage
- job id or job chip
- chunks/assets count when available
- retry or inspect-failure actions for admins

### Chat and Workspace

Use subtle status indicators only.

Show:

- small domain indexing badge near domain selector or workspace tree
- source navigator status badge for selected documents
- no admin-only lifecycle detail in normal user chat

Do not mix document-processing status with retrieval evidence cards. Evidence display and processing status are separate concerns.

## Lifecycle Action Design

Do not expose backend lifecycle verbs one-to-one as top-level UI buttons.

Avoid this flat action row:

```text
Up | Down | Recreate | Repair | Regenerate | Archive | Delete | Purge Preview | Purge
```

Preferred user-facing actions:

| User Action | UI Placement | Notes |
|---|---|---|
| Start | normal action | Maps to backend start/up behavior |
| Stop | normal action | Maps to backend stop/down behavior |
| Repair | primary recovery action | Should absorb common recreate/regenerate recovery needs if backend semantics allow |
| Advanced recreate | advanced/debug menu only | Do not show as everyday action unless truly needed |
| Advanced regenerate config | advanced/internal only | Prefer hiding from standard admin UI |
| Archive | danger-zone, reversible/destructive-low | Clear copy, not permanent |
| Preview purge | danger-zone required pre-step | Shows what will be deleted |
| Purge permanently | danger-zone final action | Requires explicit confirmation |

## Admin vs User Visual Boundaries

Admin surfaces may show:

- lifecycle state
- job queue
- failed documents
- retry actions
- purge preview
- runtime health details
- limited recent operational messages

Regular user surfaces may show:

- domain available/unavailable
- domain indexing indicator
- document still processing badge
- safe counts such as indexed/processing/failed

Regular users should not see:

- provider secrets
- raw LightRAG internals
- destructive actions
- repair/recreate/regenerate controls
- verbose backend logs

## Frontend Implementation Rules

- Use shadcn semantic tokens, not hardcoded colors.
- Prefer full block imports first; simplify only when a specific interaction, data contract, or auth boundary requires it.
- Do not create a second design system on top of shadcn.
- Do not duplicate status cards across chat, settings, and documents.
- Extract shared chips/cards only after two or more real surfaces need them.
- Keep status polling state separate from retrieval/evidence state.
- Keep Source Navigator and Context Stream visually related but conceptually separate.

## Importing shadcn Blocks

When using a shadcn block:

1. Identify the closest matching full block and import it wholesale.
2. Keep original structure, spacing, and visual treatment by default.
3. Wire the block to Context Engine data/contracts with minimal UI surgery.
4. Ensure admin-only data/actions stay behind admin-only routes.
5. Run lint/build before committing.

## Design Principle Summary

Context Engine should feel like a native shadcn application with a technical workspace personality:

- neutral by default
- color only where state matters
- compact but readable
- calm under active processing
- explicit about destructive operations
- consistent across domains, documents, jobs, chat, and source navigation

## Tooling: Using shadcn.io MCP in Cursor

Use the shadcn.io MCP server as a block-discovery and implementation-assistance tool, not as an authority to overwrite Context Engine's design system.

The purpose of MCP use is to help Cursor retrieve real shadcn.io block metadata, examples, icons, and install commands so the coding agent does not hallucinate props, paths, or component APIs.

### Recommended Cursor Setup

For individual local use, configure the MCP server globally in Cursor.

For team/project use, prefer a project-level `.cursor/mcp.json` committed with a token placeholder, not a real token.

Recommended project-safe shape:

```json
{
  "mcpServers": {
    "shadcnio": {
      "url": "https://www.shadcn.io/api/mcp?token=${SHADCNIO_TOKEN}"
    }
  }
}
```

Each developer should provide `SHADCNIO_TOKEN` through their shell or a git-ignored local environment file. Do not commit a real shadcn.io token. Treat the full MCP URL like an API key.

### Cursor Usage Rules

When asking Cursor to use shadcn.io, name the MCP server explicitly:

```text
use shadcnio to search for compact dashboard/job queue/status workflow blocks that could fit this Context Engine admin surface
```

Prefer this workflow:

1. Search for candidate blocks.
2. Inspect the block metadata and component structure.
3. Select the best-fit block and import it wholesale by default.
4. Wire data and auth constraints with minimal visual changes.
5. Run lint/build before committing.

### Approved MCP-Assisted Tasks

Use shadcn.io MCP for:

- finding dashboard, monitoring, workflow, job queue, table, danger-zone, timeline, skeleton, and empty-state patterns
- checking exact block names/slugs before installation
- retrieving install commands
- inspecting component structure before adapting it
- finding icons or small UI primitives that match an existing surface
- comparing multiple candidate blocks for the same admin workflow

Do not use shadcn.io MCP for:

- deciding backend architecture
- changing API contracts
- introducing new state management patterns
- replacing existing Context Engine routing/state boundaries
- bypassing `DESIGN.md`
- exposing LightRAG directly to the frontend
- creating a second component system outside shadcn/ui

### Context Engine Block Adaptation Checklist

Before committing any MCP-sourced block, verify:

- The block remains visually close to the original shadcn design.
- The block does not expose backend-only actions to regular users.
- The block does not duplicate an existing card/table/status component.
- The block does not create another polling loop.
- The block does not merge retrieval evidence state with processing-status state.
- The block does not make frontend calls to LightRAG.
- The block follows the simplified lifecycle action model:
  - Start
  - Stop
  - Repair
  - Archive
  - Preview purge
  - Purge permanently
- Advanced actions such as recreate/regenerate remain hidden, internal, or clearly marked as advanced/debug-only.

### Good Cursor Prompts for This Project

Use prompts like:

```text
use shadcnio to find three compact status workflow blocks. Do not install yet. Compare their structure for a LightRAG domain lifecycle card with Start, Stop, Repair, Archive, Preview purge, and Purge permanently actions.
```

```text
use shadcnio to inspect a dashboard job queue block. Adapt only the table and status chip structure for Context Engine jobs. Keep existing API client and store boundaries. Do not add a new polling loop.
```

```text
use shadcnio to find a danger-zone block. Adapt it for Archive, Preview purge, and Purge permanently. Use existing shadcn tokens and require explicit confirmation for purge.
```

Avoid prompts like:

```text
wire this block directly to LightRAG APIs
```

### Dependency and File Hygiene

If a block installation adds files under `components/ui/`, review every generated file before committing.

Keep app-specific composites near the feature surface first, for example:

```text
client/src/components/settings/lightrag/DomainLifecycleCard.tsx
client/src/components/settings/lightrag/DomainProcessingStatusCard.tsx
client/src/components/settings/lightrag/DomainDangerZone.tsx
```

Only promote a component to a shared location after at least two real Context Engine surfaces use it.

### Token and Security Rules

- Do not commit a real shadcn.io MCP token.
- Do not paste a real MCP URL with token into documentation, issues, screenshots, or prompts.
- Prefer `${SHADCNIO_TOKEN}` placeholders in project config.
- Keep `.env` files and local token files ignored by git.
- If a token is accidentally committed, rotate/revoke it immediately.

### Final Rule

MCP should speed up accurate shadcn block discovery. It should not weaken Context Engine's architecture boundaries, auth model, polling model, or frontend/backend contracts.
