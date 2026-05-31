# Context Engine WebUI Component Inventory and Design Extraction

This inventory summarizes the current WebUI surface and the shadcn-style primitives to preserve while flattening the visual language.

## 1. Current stack signals

- `client/components.json` uses shadcn `new-york` style, TypeScript, RSC, Tailwind CSS variables, neutral base color, aliases to `@/components/ui`, and `lucide` icons.
- `client/src/app/globals.css` already defines a graphite-like token base: white canvas, near-black foreground, muted graphite surfaces, neutral borders, and dark mode tokens.
- The client is Next.js/React with local component ownership, which aligns well with a customized shadcn system.

## 2. shadcn-style primitives currently present

Core primitives in `client/src/components/ui`:

- `alert-dialog.tsx`
- `badge.tsx`
- `button.tsx`
- `card.tsx`
- `checkbox.tsx`
- `command.tsx`
- `dialog.tsx`
- `dropdown-menu.tsx`
- `input.tsx`
- `label.tsx`
- `popover.tsx`
- `select.tsx`
- `switch.tsx`
- `table.tsx`

Design implication: keep this primitive layer. Do not add a parallel UI kit. Modify tokens and composition patterns first.

## 3. App-specific shell components

Layout:

- `AppLayout.tsx`
- `AppPageFrame.tsx`

Chat/RAG workspace:

- `LightRagChatShell.tsx`
- `ChatComposer.tsx`
- `ConversationView.tsx`
- `MessageBubble.tsx`
- `RetrievalSettingsPopover.tsx`
- `SidePanel.tsx`
- `WorkspaceTree.tsx`
- `ConnectionControl.tsx`

Tree primitive:

- `components/reui/tree.tsx`

Settings/account route:

- `app/settings/users/page.tsx`
- imported `AccountSettingsPanel` path indicates settings panels should remain route-like and admin-aware.

## 4. Main UI surfaces to preserve

### 4.1 Chat shell

Current role:

- Loads LightRAG domains.
- Applies selected domain defaults.
- Retrieves evidence and adapted assistant response.
- Loads workspace tree for selected domain.
- Controls evidence/context side panel.

Design extraction:

- Keep the three-zone workspace pattern.
- Make domain context visible in the top/composer region.
- Keep empty state calm: “Ask your knowledge graph.”
- Use accent only for selected domain, selected source, progress, and citation numbers.

### 4.2 Composer

Current role:

- Multiline text input.
- Send button.
- Retrieval settings popover.
- Admin upload entry point.

Design extraction:

- Keep the composer flat and pill/rounded.
- Do not add AI sparkle decoration.
- Use a quiet plus/upload affordance only for admin.
- Retrieval settings remains a popover-level control, not a full settings page.

### 4.3 Evidence side panel

Current role:

- Resizable right context panel.
- Shows retrieval summary, pipeline progress, text/table/figure context items.
- Provides empty/loading/error states.

Design extraction:

- Treat the side panel as a core product surface, not optional decoration.
- Add compact citation map at the top.
- Keep evidence cards compact and document-first.
- Make table/figure evidence visibly different but not colorful.

### 4.4 Workspace tree

Current role:

- Shows source/document tree via headless-tree and local tree primitive.

Design extraction:

- Keep file-explorer grammar.
- Use selected row soft accent + left rail/dot.
- Do not turn tree rows into cards.

### 4.5 Settings/admin surfaces

Current role:

- Account/user administration exists as a settings route/fallback.
- Desired routes include Providers, Models, LightRAG Domains, Documents, Status, Logs.

Design extraction:

- Use a modal/dialog shell with left route navigation.
- Prefer settings rows with dividers over nested cards.
- Cards are only for provider/domain/status objects.
- Admin-only actions should be visibly controlled and confirmed.

## 5. Flattening rules for current UI

### Remove or avoid

- Nested fieldset borders for simple radio groups.
- Card-within-card layouts in settings.
- Multiple borders around a single workflow.
- Decorative badges with no operational meaning.
- Large tinted panels.

### Keep

- Outer dialog/panel/card borders.
- Input/select affordance borders.
- Row dividers in repeated lists.
- Selected-state rail/dot.
- Monospace metadata.

## 6. Component mapping to preview package

The standalone preview includes realistic examples for:

- shadcn Card: domain, provider, evidence, status summary.
- Button variants: primary, secondary, quiet, control, destructive text action.
- Badge/chip variants: selected domain, source count, status, admin-only.
- Input/select/textarea: domain create form and retrieval settings.
- Dialog-like panel: create knowledge graph domain.
- Popover-like block: retrieval settings.
- Table/list: LightRAG domain lifecycle status.
- Workspace tree: document/source map.
- Context panel: evidence cards with compact citation map.

## 7. Recommended next implementation steps

1. Add graphite + accent tokens to `globals.css` without changing component behavior.
2. Update button radius toward pill for normal actions while preserving icon button geometry.
3. Flatten settings forms by removing non-interactive internal group borders.
4. Introduce `SettingsRow`, `DisclosureRow`, and `FlatRadioGroup` components.
5. Introduce `EvidenceCard` and `CitationMap` as reusable product components.
6. Use preview package to select one accent theme before production styling changes.
