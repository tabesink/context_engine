# DESIGN.md — Context Engine UI Design System

> **Purpose:** Define the product design language for the Context Engine WebUI. The system should feel like a calm, flat, graphite technical workspace inspired by Ollama’s quiet grayscale minimalism, but adapted for a production multi-user RAG application with admin settings, provider configuration, LightRAG domain lifecycle management, workspace navigation, evidence display, and operational status reporting.

---

## 0. Product Design Positioning

Context Engine should feel like a **calm technical workspace**, not a flashy AI demo.

The interface should communicate:

- **Trust** — retrieval evidence, ingestion state, and admin actions must be legible.
- **Low entropy** — every surface should feel predictable, reusable, and built from a small component grammar.
- **Quiet power** — advanced RAG/admin capabilities should be available without clutter.
- **Operational clarity** — users should always understand which domain they are querying, what evidence was returned, and what system state they are looking at.
- **Flat confidence** — use spacing, alignment, typography, and thin dividers before adding boxes, shadows, or saturated color.

The visual direction borrows Ollama’s restraint:

- graphite / neutral-first palette
- pure white or near-black surfaces
- no gradients
- no decorative color
- almost no elevation
- pill-shaped controls
- 12px container radius
- strong whitespace
- typography-led hierarchy
- minimal internal boundaries

This is not a marketing landing page. This is a **work application**. The design system must support dense operational UI while remaining quiet.

---

## 1. Core UI Principles

### 1.1 Calm by Default

The default UI should be quiet. Nothing should look urgent unless it is truly actionable.

Use subdued surfaces, thin dividers, small metadata, and restrained text weights. Prefer structure over decoration.

### 1.2 Flatten Before Decorating

When a view feels visually busy, remove internal boxes first.

Use this hierarchy:

1. spacing
2. typography
3. alignment
4. row dividers
5. soft surface shift
6. border
7. color
8. elevation

Borders should exist only when they clarify interaction or containment. Avoid card-within-card layouts unless the nested surface represents a separate object, status group, or destructive decision.

### 1.3 Evidence First

Because this app is a RAG/context engine, evidence is not secondary decoration. Evidence cards, citation maps, source paths, chunk IDs, document titles, retrieved snippets, and images/tables must be easy to scan.

The user should always be able to answer:

1. Which knowledge graph/domain am I querying?
2. What evidence was retrieved?
3. Where did this evidence come from?
4. How confident/actionable is this answer?
5. What document or artifact can I open next?

### 1.4 Admin Actions Must Feel Controlled

Admin surfaces include provider setup, API key entry, embedding model selection, LightRAG domain lifecycle controls, document upload, ingestion, and status reporting.

These actions should never feel like casual chat actions. Use clear grouping, confirmation affordances, disabled states, and status rows.

### 1.5 Use Layout Instead of Color

Do not rely on chromatic color to create hierarchy. Use:

- spacing
- dividers
- text weight
- background contrast
- icon shape
- position
- pill labels
- monospace metadata

### 1.6 Color Is a Hint, Not the Structure

Context Engine remains grayscale-first. Accent color is allowed, but only as a quiet product hint.

Use accent color for:

- selected state indicators
- active tabs/nav rails
- progress fill
- citation numbers
- selected domain/provider chips
- focus-adjacent emphasis where grayscale alone is insufficient

Do not use accent color for:

- full-card backgrounds
- large decorative panels
- gradients
- unrelated badges
- every icon

Status colors may be used only if the implementation has accessible semantic tokens and the state is operationally important. Color must never be the only state indicator. Always pair with text and iconography.

---

## 2. Visual Theme

### 2.1 Overall Atmosphere

The UI should feel like a clean technical instrument:

- pure white primary canvas
- soft graphite panels
- crisp 1px borders
- no default drop shadows
- no gradients
- no decorative illustrations
- compact but breathable admin layouts
- flat sectioning with fewer internal boundaries

Avoid the common “AI SaaS dashboard” look: no purple gradients, glowing cards, glassmorphism, animated blobs, heavy shadows, or colorful badge overload.

### 2.2 Geometry

Use a binary radius system:

| Element Type | Radius | Notes |
|---|---:|---|
| Interactive controls | `9999px` | buttons, tabs, input wrappers, chips, badges, dropdown triggers |
| Containers | `12px` | panels, cards, dialogs, drawers, evidence cards, code blocks |
| Nested small containers | `8px` | only inside dense operational panels where 12px feels too bulky |
| Raw table/list rows | `0px` or inherited | use dividers, not card bubbles |

Default rule: **pill for actions, 12px for containers, dividers for internal separation.**

### 2.3 Depth

Do not use shadows as the default depth system.

| Level | Treatment | Use |
|---|---|---|
| Canvas | no border, no shadow | app background |
| Section | subtle background only | sidebars, panels |
| Divided | top/bottom divider | settings rows, logs, tables |
| Bordered | `1px solid var(--border)` | external cards, dialogs, inputs, evidence objects |
| Selected | `var(--accent-soft)` or `var(--surface-muted)` + left border/dot | selected nav item, selected domain |
| Modal | border + backdrop | settings dialog and confirmation dialogs |

Shadow exception: a very subtle shadow may be used for floating popovers/dropdowns only if needed for readability. Do not use shadows on normal cards.

### 2.4 Internal Boundary Rule

When designing a form, modal, card, or panel:

- keep the outer container boundary
- keep boundaries on controls that require affordance, such as inputs/selects
- remove nested fieldset borders unless the group represents a distinct mode or risk area
- prefer section labels plus whitespace over boxed groups
- use dividers only when the eye needs a pause between repeated rows

Example: In a “Create knowledge graph domain” form, keep the dialog border and input borders, but remove the internal bordered host-port box. Render host-port as a simple radio group with a label and helper text.

---

## 3. Color System

### 3.1 Graphite Base Tokens — Light Mode

| Token | Value | Use |
|---|---:|---|
| `--background` | `#ffffff` | main app canvas |
| `--foreground` | `#1d1d1f` | primary text |
| `--surface` | `#ffffff` | cards/panels |
| `--surface-muted` | `#f7f7f8` | sidebars, selected rows, subtle sections |
| `--surface-raised` | `#f2f2f4` | active chips, compact rows |
| `--border` | `#e8e8ed` | default border |
| `--border-strong` | `#d4d4dc` | focused/active border |
| `--muted` | `#737373` | secondary text |
| `--muted-strong` | `#525252` | emphasized secondary text |
| `--muted-faint` | `#a3a3a8` | placeholders, timestamps |
| `--control` | `#f5f5f7` | gray button background |
| `--control-hover` | `#ececef` | gray button hover |
| `--inverse` | `#1d1d1f` | black CTA |
| `--inverse-foreground` | `#ffffff` | text on black CTA |
| `--focus-ring` | `rgba(59, 130, 246, 0.5)` | keyboard focus ring only |

### 3.2 Graphite Base Tokens — Dark Mode

| Token | Value | Use |
|---|---:|---|
| `--background` | `#0f0f10` | main app canvas |
| `--foreground` | `#f4f4f5` | primary text |
| `--surface` | `#151517` | cards/panels |
| `--surface-muted` | `#1c1c1f` | sidebars, selected rows |
| `--surface-raised` | `#242428` | active chips, compact rows |
| `--border` | `#2d2d32` | default border |
| `--border-strong` | `#44444c` | focused/active border |
| `--muted` | `#b2b2b8` | secondary text |
| `--muted-strong` | `#d7d7db` | emphasized secondary text |
| `--muted-faint` | `#777780` | placeholders, timestamps |
| `--control` | `#1c1c1f` | gray button background |
| `--control-hover` | `#242428` | gray button hover |
| `--inverse` | `#f4f4f5` | inverted CTA |
| `--inverse-foreground` | `#0f0f10` | text on inverted CTA |
| `--focus-ring` | `rgba(96, 165, 250, 0.55)` | keyboard focus ring only |

### 3.3 Graphite + Accent Theme Options

These are preview themes, not mandatory brand decisions. They should be explored in the standalone preview before implementation.

| Theme | Accent | Accent Strong | Accent Soft | Accent Border | Accent Text | Best Use |
|---|---:|---:|---:|---:|---:|---|
| Graphite Teal | `#4f8f83` | `#2f6f65` | `#eef6f4` | `#cfe3df` | `#275f57` | Recommended default; technical, calm, operational |
| Graphite Indigo | `#6d6adf` | `#504dc4` | `#f1f1fb` | `#dadaf5` | `#4643a8` | Slightly more “software platform” feel |
| Graphite Sage | `#71816d` | `#53634f` | `#f2f5f1` | `#d8e0d5` | `#495c45` | Quietest and most Ollama-adjacent |
| Graphite Amber | `#b9823b` | `#8f6329` | `#fbf5ec` | `#ead8bd` | `#754f20` | Good for admin/attention emphasis; risky as global accent |
| Graphite Steel | `#5b7894` | `#3f5f78` | `#f0f5f8` | `#d2e0e8` | `#34546b` | Balanced enterprise/engineering tone |

Accent implementation tokens:

```css
:root {
  --ce-accent: #4f8f83;
  --ce-accent-strong: #2f6f65;
  --ce-accent-soft: #eef6f4;
  --ce-accent-border: #cfe3df;
  --ce-accent-text: #275f57;
}
```

### 3.4 Status Treatment

Prefer grayscale operational states with text:

| State | Visual Treatment | Required Text |
|---|---|---|
| Healthy / Ready | solid dot + `Ready` | `Ready` |
| Processing | spinner or pulsing dot + `Ingesting` | `Ingesting` |
| Queued | hollow dot + `Queued` | `Queued` |
| Warning | triangle icon + `Needs attention` | explain reason |
| Error | x icon + `Error` | explain reason |
| Disabled | muted icon + `Disabled` | explain why |
| Archived | archive icon + `Archived` | show restore/delete options |

If semantic colors are used, keep them small: dots, icons, progress fills, and text labels. Do not tint entire cards red/green.

---

## 4. Typography

### 4.1 Font Families

```css
--font-display: "SF Pro Rounded", ui-rounded, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
--font-sans: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
--font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
```

### 4.2 Type Scale

| Role | Size | Weight | Line Height | Use |
|---|---:|---:|---:|---|
| App Title | 28–32px | 500 | 1.15 | page titles, modal titles |
| Section Title | 20–24px | 500 | 1.25 | settings panels, workspace sections |
| Subsection Title | 16–18px | 500 | 1.35 | row groups, card headers |
| Body | 14–16px | 400 | 1.5 | default UI text |
| Body Emphasis | 14–16px | 500 | 1.5 | labels, selected nav |
| Caption | 12–13px | 400 | 1.4 | metadata, helper text |
| Mono Body | 13–14px | 400 | 1.45 | IDs, paths, commands |
| Mono Small | 11–12px | 400 | 1.35 | chunk IDs, hashes, compact metadata |

### 4.3 Typography Rules

- Use display font sparingly. It is for high-level headings, not every label.
- Avoid bold weights. Use 500 for emphasis.
- Use monospace for technical identity: document IDs, chunk IDs, API routes, container names, ports, paths, and job IDs.
- Keep evidence snippets to 55–75 characters per line.
- Do not center-align operational UI. Use left alignment for settings, tables, evidence, logs, and workspace trees.

---

## 5. App Shell Layout

The main WebUI should be a three-zone workspace:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Top Bar: domain selector | retrieval settings | status | account/settings    │
├───────────────┬─────────────────────────────────────────────┬───────────────┤
│ Workspace     │ Main Workspace / Chat                       │ Context Panel │
│ Tree          │                                             │ Evidence      │
│               │ Ask composer                               │ Citations     │
│ Documents     │ Answer / canvas / selected document         │ Tables/Images │
└───────────────┴─────────────────────────────────────────────┴───────────────┘
```

### 5.1 Top Bar

Use a low-height, border-bottom top bar.

Required items:

- current workspace/domain selector
- retrieval settings button
- ingestion/status indicator
- settings button
- account menu

Treatment:

- no heavy background
- `height: 56px` desktop
- 1px bottom border
- pill controls
- selected LightRAG domain visible as a quiet accented pill

### 5.2 Workspace Tree

Purpose: show documents and local navigation for the selected LightRAG domain.

Style:

- left panel width: `260–320px`
- background: `--surface-muted`
- right border: `1px solid --border`
- tree rows: 32–36px height
- selected row: soft accent background + left accent rail or dot
- document titles: plain sans
- technical IDs: caption/mono only when needed
- icons should be monochrome and functional

Do not over-card the tree. It should feel like a file explorer, not a dashboard grid.

### 5.3 Main Workspace

The center area supports:

- chat question input
- answer rendering
- selected document/page/section preview
- workspace state messages

Design:

- maximum readable content width inside center panel
- composer anchored near bottom or naturally after answer
- large empty state when no query exists
- answer body should not compete visually with evidence panel

### 5.4 Context / Evidence Panel

Right panel width: `340–440px`, resizable up to `720px` if needed.

Purpose: show evidence returned by retrieval and populate context details.

The evidence panel should support:

- compact citation map
- evidence cards
- document/title/source path
- snippet text
- score/rank metadata
- images/tables/artifacts
- jump/open actions

Do not hide evidence behind an extra click. The right panel is a core product surface.

---

## 6. Settings Dialog

Settings should be a modal or large dialog with left navigation and route-like sections.

```text
┌───────────────────────────────────────────────────────────────┐
│ Settings                                                Close │
├───────────────┬───────────────────────────────────────────────┤
│ Account       │ Section Title                                │
│ Providers     │ Helper text                                  │
│ Models        │                                               │
│ LightRAG      │ [Rows / cards / forms]                        │
│ Documents     │                                               │
│ Status        │                                               │
│ Logs          │                                               │
└───────────────┴───────────────────────────────────────────────┘
```

### 6.1 Settings Navigation

Routes:

1. **Account**
   - retain admin-driven user creation/modification
   - current user details
   - role visibility

2. **Providers**
   - replaces old “LLM Model” route
   - configure provider connections
   - API key entry
   - OpenAI-compatible providers
   - AWS Bedrock OpenAI-compatible endpoint
   - local Ollama service

3. **Models**
   - embedding model selection
   - LLM model selection
   - default model assignment
   - admin-only write access

4. **LightRAG Domains**
   - create domain
   - start/stop/archive/delete domain
   - port/container/status display
   - domain-specific embedding model lock

5. **Documents**
   - upload to selected domain
   - ingestion jobs
   - file/artifact status
   - images/tables extracted

6. **Status**
   - app health
   - LightRAG domain health
   - Redis/Postgres status
   - queue/job status

7. **Logs**
   - recent operational events
   - filter by domain/job/document
   - copy diagnostic bundle

### 6.2 Settings Layout Rules

- Use rows for configuration, not oversized cards.
- Use cards only for domain objects, provider objects, or grouped status objects.
- Each row should have label, helper text, and control on right.
- Use dividers between repeated rows.
- Avoid nested modal chains.
- Keep destructive actions right-aligned and visually restrained.
- Every admin-only action should be hidden for non-admin routes or disabled with explanation for individual actions.

### 6.3 Settings Row Pattern

```text
Embedding model
Fixed model used for document ingestion in this domain.       [text-embedding-3-large v]
───────────────────────────────────────────────────────────────────────────────
LLM provider
Provider used for answer generation and reasoning.            [OpenAI v]
```

Implementation guidance:

- label: 14–16px, weight 500
- helper: 12–13px muted
- control: pill/select/button
- row padding: 16px 0
- divider: 1px border
- no extra row card unless the row is itself an object summary

---

## 7. Provider and Model Configuration UI

### 7.1 Provider Route

Provider cards should be compact and operational:

```text
OpenAI                                                    Connected
OpenAI API-compatible provider for hosted models.
Base URL: https://api.openai.com/v1                         [Configure]
```

Use a light bordered provider object only when multiple providers are being compared. Inside a provider object, use rows and dividers instead of nested cards.

Supported providers for now:

- OpenAI
- AWS Bedrock OpenAI-compatible endpoint
- Ollama local service

Do not create a giant provider marketplace UI. This app needs controlled provider setup.

### 7.2 API Key Entry

API key fields should:

- use password masking
- support “test connection”
- show last validated timestamp
- never reveal full secret after save
- use monospace for base URLs and model IDs
- show inline errors in plain language

### 7.3 Embedding Model Lock

When creating a LightRAG domain, embedding model choice is a **domain-level irreversible compatibility decision** unless the domain is re-indexed.

UI copy should be explicit:

> The embedding model is locked for this domain after ingestion starts. Mixing embedding models in one vector store can corrupt retrieval quality. To change the embedding model later, create a new domain or re-index this domain.

### 7.4 Create Knowledge Graph Domain Form

Use the flatter treatment:

```text
Create knowledge graph domain
Create an isolated retrieval domain for documents and evidence.

Domain identity
Domain ID                         Display name
[ fatigue                      ]  [ Fatigue Manuals              ]

Embedding model
[ openai · text-embedding-3-small · 1536 dims                  v]
Locked after creation. Documents in this domain share the same embedding space.

Host port
(●) Auto-assign available port
( ) Use custom port

Advanced retrieval defaults                                      chevron-down

                                                          [Cancel] [Create]
```

Rules:

- no bordered fieldset around host port
- advanced retrieval defaults should be a lightweight disclosure row
- keep input/select boundaries for affordance
- use accent only for selected radio state or active selector
- keep the primary Create button high contrast

### 7.5 LLM Model Flexibility

LLM models are not locked like embedding models. They can be changed globally or per retrieval/session if product requirements allow.

UI should communicate:

- embedding model = ingestion compatibility
- LLM model = answer generation behavior

---

## 8. LightRAG Domain Lifecycle UI

Domain management should be clear enough for a junior admin to operate safely.

### 8.1 Domain Object Pattern

```text
manufacturing-qa                                      ● Ready
Port 9622 · OpenAI embeddings · 128 documents · 4.2GB
Last indexed 2026-05-27 09:40

[Open] [Upload documents] [Restart] [Archive]
```

This can be a Card if it is one of several domain objects. Do not put sub-cards inside it.

### 8.2 Domain States

| State | Description | Primary Action |
|---|---|---|
| Draft | Created but not running | Start |
| Starting | Container/service booting | View logs |
| Ready | Queryable | Open / Upload |
| Ingesting | Documents being indexed | View jobs |
| Degraded | Running with warnings | Diagnose |
| Error | Failed startup/retrieval | View logs / Retry |
| Stopped | Not running | Start |
| Archived | Removed from active list | Restore / Delete |

### 8.3 Destructive Actions

Archiving and deletion must be distinct.

- **Archive**: remove from active use; preserve recoverable data unless retention policy says otherwise.
- **Delete**: remove domain data, uploaded files, derived artifacts, images/tables, vector/graph stores, and job history according to retention policy.

For delete confirmation, require the domain name to be typed.

---

## 9. Document Upload and Ingestion UI

### 9.1 Upload Surface

Upload should be domain-bound. The selected domain must be obvious.

```text
Upload documents to: manufacturing-qa
Embedding model: text-embedding-3-large

[ Drop files here or choose files ]

Supported: PDF, DOCX, Markdown, TXT
```

### 9.2 Ingestion Job Rows

```text
suspension-report.pdf                                  Ingesting
Parsing pages 12/48 · extracting tables/images
███████████████░░░░░░░░░░ 56%
Job: ingest_01HX... · Started 09:41
```

Use rows with dividers when jobs are in a list. Use a Card only when showing a standalone job detail.

### 9.3 Artifact Visibility

If documents generate images, tables, thumbnails, or extracted files, surface them as first-class artifacts under the document.

```text
Document
├─ Text chunks
├─ Tables
│  ├─ Table 1 — material properties
│  └─ Table 2 — test results
└─ Figures
   ├─ Figure 1 — process flow
   └─ Figure 2 — stress map
```

---

## 10. Evidence Panel Design

Evidence should use a compact card or row-card pattern.

### 10.1 Evidence Panel Header

```text
Evidence
7 sources · manufacturing-qa · hybrid retrieval

[Ranked] [Documents] [Tables] [Images]
```

### 10.2 Compact Citation Map

Use a small citation map at the top for scannability.

```text
Citation map
[1] suspension-report.pdf     p.12   chunk_183
[2] forging-notes.md          §3     chunk_044
[3] material-table.xlsx       T2     table_002
```

Rules:

- use monospace for citation IDs and chunk IDs
- show document title first
- show location second
- show source type where helpful
- make rows clickable
- use accent for citation number pills, not the whole row

### 10.3 Evidence Card

```text
[1] suspension-report.pdf                              p.12
“The optimized preform reduced flash while maintaining...”

chunk_183 · score 0.82 · hybrid
[Open source] [Copy citation]
```

Required evidence fields for stable rendering:

- `reference_id`
- `document_title`
- `source_path`
- `chunk_id`
- `content`
- `score`
- `retrieval_method`
- `metadata`

Recommended optional fields:

- `page_number`
- `section_title`
- `artifact_type`
- `image_url`
- `table_id`
- `bbox`
- `created_at`
- `domain_id`

### 10.4 Evidence with Images/Tables

Image/table evidence should remain compact.

```text
[4] process-flow.pdf                                Figure 2
┌──────────────────────────────────────────────────────────┐
│ image/table preview                                      │
└──────────────────────────────────────────────────────────┘
Caption: Billet heating and transfer workflow.
figure_002 · p.7 · score 0.76
[Open] [Use in answer] [Copy citation]
```

---

## 11. Chat Composer and Retrieval Settings

### 11.1 Composer

The composer should be simple and persistent.

```text
Ask your knowledge graph...
[ message input                                      ] [Send]
[Domain: manufacturing-qa] [Retrieval settings]
```

Composer rules:

- use pill input if single-line
- use 12px container if multiline
- send button is black pill/icon button
- retrieval settings are a quiet secondary pill
- do not overdecorate with AI sparkle icons

### 11.2 Retrieval Settings

Retrieval settings should be accessible but not overwhelming.

Suggested controls:

- domain selector
- retrieval mode: hybrid / semantic / graph
- top-k
- include images/tables toggle
- reranking toggle if available
- model override if allowed

Use a popover or settings drawer. Avoid full-page configuration for frequent retrieval settings.

---

## 12. Status Reporting UI

Status reporting should be operationally useful, not decorative.

### 12.1 Status Summary

```text
System status
App Ready · Postgres Ready · Redis Ready · 3 LightRAG domains running
```

### 12.2 Status Cards

```text
LightRAG Domains                                      3 Ready
manufacturing-qa     Ready       port 9622
policies             Ingesting    4 jobs queued
archived-test        Stopped      archived
```

### 12.3 Logs

Logs should be readable and filterable.

```text
09:41:22  ingest.started     suspension-report.pdf
09:42:10  parse.complete     48 pages
09:42:33  lightrag.upsert    183 chunks
09:43:01  ingest.complete    Ready
```

Use monospace for event names and IDs. Use normal sans for explanations.

---

## 13. Component Grammar

### 13.1 shadcn Foundation

The app should continue using the local shadcn-style primitive layer. Keep the component surface small and composable.

Current / target primitive families:

- `AlertDialog`
- `Badge`
- `Button`
- `Card`
- `Checkbox`
- `Command`
- `Dialog`
- `DropdownMenu`
- `Input`
- `Label`
- `Popover`
- `Select`
- `Switch`
- `Table`
- tree primitives for workspace/source navigation

### 13.2 Buttons

| Variant | Background | Border | Text | Use |
|---|---|---|---|---|
| Primary | `--inverse` | `--inverse` | `--inverse-foreground` | main action |
| Secondary | `--surface` | `--border-strong` | `--foreground` | secondary action |
| Quiet | transparent | transparent | `--muted-strong` | low-priority action |
| Control | `--control` | `--control` | `--foreground` | normal in-panel action |
| Destructive | `--surface` | `--border-strong` | `--foreground` | destructive action with clear text |

Do not use bright red destructive buttons by default. Use text, icon, confirmation, and placement to communicate risk. If semantic red is introduced, use it only in confirmation/error contexts.

### 13.3 Inputs

- radius: pill for short fields/search/select triggers
- radius: 12px for textareas and code/API key blocks
- border: `1px solid --border`
- focus: `--focus-ring`
- placeholder: `--muted-faint`
- helper/error text below input

### 13.4 Cards

Cards should be functional containers, not decorative tiles.

- background: `--surface`
- border: `1px solid --border`
- radius: 12px
- padding: 16–24px
- no shadow
- hover only when clickable

Card should be used for:

- domain object
- provider object
- evidence object
- status summary group
- modal/dialog surfaces

Card should not be used for:

- every settings row
- every tree item
- every log line
- every form subsection
- nested host-port/radio groups

### 13.5 Tables and Lists

Prefer lists for domain/status rows. Use tables only when comparison matters.

Table rules:

- no zebra striping unless density requires it
- 1px row dividers
- compact row height: 40–48px
- monospace for IDs/ports/job IDs
- right-align numeric metrics where appropriate

### 13.6 Badges and Chips

- pill radius
- muted background
- caption text
- icon optional
- no saturated color
- avoid badge overload
- use accent chips only for selected/current state

---

## 14. Empty, Loading, Error, and Permission States

### 14.1 Empty State

```text
No documents in this domain yet.
Upload documents to build the workspace tree and retrieval index.

[Upload documents]
```

### 14.2 Loading State

Use skeleton rows or simple spinners. Avoid playful animations.

### 14.3 Error State

Errors must be plain language.

Bad:

> Request failed.

Good:

> The domain start request returned HTTP 200, but the operation result was `error`. View the domain logs for the container startup failure.

### 14.4 Permission State

For non-admin users:

```text
Admin access required.
You can query existing knowledge graph domains, but only admins can upload documents or manage LightRAG lifecycle settings.
```

---

## 15. Accessibility

Minimum requirements:

- keyboard navigable settings, dialogs, menus, and tree
- visible focus ring
- no color-only status
- 44px minimum touch targets for primary controls
- aria labels for icon-only buttons
- dialog focus trap
- Escape closes popovers/dialogs
- reduced motion respected
- high contrast between text and background
- truncation must provide full value on hover/title or copy action

---

## 16. Responsive Behavior

### Desktop First

This app is primarily a desktop technical workspace.

Desktop layout:

- top bar
- left workspace tree
- center workspace
- right evidence panel

### Tablet

- collapsible left tree
- right evidence panel can become drawer
- settings remains modal/full-height drawer

### Mobile

Mobile should be usable for review, not full admin operation.

- tree becomes drawer
- evidence becomes bottom sheet or separate tab
- settings becomes full-screen
- tables convert to stacked rows
- domain/status actions remain accessible but compact

---

## 17. Implementation Guidance

### 17.1 Token-First CSS

Create tokens once and consume them everywhere.

Example:

```css
:root {
  --background: #ffffff;
  --foreground: #1d1d1f;
  --surface: #ffffff;
  --surface-muted: #f7f7f8;
  --border: #e8e8ed;
  --border-strong: #d4d4dc;
  --muted: #737373;
  --muted-faint: #a3a3a8;
  --control: #f5f5f7;
  --inverse: #1d1d1f;
  --inverse-foreground: #ffffff;
  --ce-accent: #4f8f83;
  --ce-accent-soft: #eef6f4;
  --ce-accent-border: #cfe3df;
  --ce-accent-text: #275f57;
}
```

### 17.2 Reusable Components to Prioritize

Build and reuse these before inventing new layout patterns:

1. `AppShell`
2. `TopBar`
3. `WorkspaceTree`
4. `ContextPanel`
5. `EvidenceCard`
6. `CitationMap`
7. `SettingsDialog`
8. `SettingsNav`
9. `SettingsRow`
10. `ProviderCard`
11. `DomainCard`
12. `StatusRow`
13. `JobProgressRow`
14. `EmptyState`
15. `ConfirmDialog`
16. `FlatRadioGroup`
17. `DisclosureRow`
18. `ObjectList`

### 17.3 Avoid One-Off UI

Do not create separate visual patterns for:

- domain rows
- document rows
- job rows
- status rows

They should share a common row/list grammar.

### 17.4 Standalone Preview Before Main App Changes

Use the standalone preview package to compare accent palettes and component treatments before changing production components. The preview is intentionally static and should not import app code or touch backend APIs.

---

## 18. Do / Don’t

### Do

- Use graphite-first semantic tokens.
- Use accent as a subtle hint.
- Use 12px containers and pill controls.
- Use no shadows except rare popovers.
- Keep settings row-based and readable.
- Make evidence visible and scannable.
- Show selected domain everywhere it matters.
- Use clear admin/non-admin states.
- Use text labels with status icons.
- Use monospace for technical metadata.
- Keep destructive actions explicit and confirmed.
- Remove nested boxes when whitespace and labels are enough.

### Don’t

- Do not add colorful AI gradients.
- Do not turn every object into a card.
- Do not box every form subsection.
- Do not hide evidence behind vague “sources” toggles.
- Do not make admin lifecycle actions look casual.
- Do not use semantic color as the only state cue.
- Do not use heavy shadows or glassmorphism.
- Do not mix multiple radius systems.
- Do not scatter raw hex values across components.
- Do not make the WebUI parse deeply nested metadata for core evidence display.

---

## 19. Acceptance Checklist

A UI change follows this design system if:

- [ ] It uses semantic tokens, not raw colors.
- [ ] It preserves graphite-first visual language.
- [ ] It uses accent only for selected/current/active hints.
- [ ] It uses pill controls and 12px containers.
- [ ] It removes unnecessary internal boundaries.
- [ ] It has no decorative gradients/shadows.
- [ ] It works in light and dark mode.
- [ ] It has keyboard focus states.
- [ ] It uses reusable row/card/dialog patterns.
- [ ] It clearly shows domain context where relevant.
- [ ] It makes evidence and citations scannable.
- [ ] It handles empty/loading/error/permission states.
- [ ] It distinguishes admin-only actions.
- [ ] It avoids duplicating component patterns.

---

## 20. Agent Prompt Addendum

When asking a coding agent to implement UI in this project, include this instruction:

> Follow `DESIGN.md` strictly. Build a quiet, flat graphite technical workspace inspired by Ollama, not a colorful AI SaaS dashboard. Use tokenized colors, no gradients, no decorative shadows, pill controls, 12px containers, row-based settings, visible evidence cards, compact citation maps, and clear admin-only lifecycle controls. Prefer reusable layout primitives over one-off UI. Remove unnecessary internal boundaries. Every operational state must have text, not just color. Use the standalone preview package to compare Graphite + accent themes before touching the main app.
