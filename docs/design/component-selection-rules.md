# Component Selection Rules

## Component Research Output

For every meaningful UI surface change, the component researcher must produce `specs/<surface>/component-research.md` with:

1. Candidate blocks/components.
2. Why each candidate fits the surface.
3. Which existing capability each candidate preserves.
4. Required install commands, if any.
5. Component composition plan.
6. Accessibility notes.
7. Responsive layout notes.
8. Rejected alternatives and why they were rejected.

## Selection Heuristics

### Use Cards When Users Evaluate Objects

Examples:

- Provider cards.
- Domain cards.
- Document processing summaries.
- Figure/table evidence previews.

Card content should include a title, short metadata, status badge, primary action, and secondary action menu when needed.

### Use Tables When Users Scan Dense Admin State

Examples:

- Providers and model availability.
- Documents and ingestion jobs.
- Domain lifecycle operations.
- Audit-like status records.

Tables should include compact badges and row actions. Avoid turning dense data into oversized cards.

### Use Tabs For Two Or Three Peer Views

Examples:

- Context Stream vs Source Navigation in the right panel.
- Provider configuration vs model list vs health/status.
- Domain overview vs documents vs jobs.

Do not use tabs to hide unrelated workflows.

### Use Inline Panels For Primary Forms

For major settings forms, use persistent inline panels/cards. Avoid opening a sheet for important configuration if the design intent says the form should remain visible and editable on the page.

### Use Dialogs For Confirmation, Not Exploration

Dialogs are appropriate for destructive confirmation and short credential/API-key input scoped to a selected provider. Do not use dialogs for long multi-section configuration flows.

### Use Dropdown Menus For Secondary Row Actions

Examples:

- Repair domain.
- Recreate container.
- Archive/delete.
- Purge preview.
- Retry ingestion.

Primary actions should remain visible. Dangerous secondary actions should be grouped and confirmed.

## Context Engine Surface Recommendations

### Providers Settings Surface

Recommended composition:

- `SurfaceHeader` with title, description, and admin-only status.
- Tabs or segmented control for `Providers`, `Models`, and `Health` if the surface is dense.
- Provider cards or compact provider rows for high-level provider selection.
- Inline config form for the selected provider.
- Model table for available LLM/embedding models.
- Alert for embedding model immutability after documents are ingested.

### Domain Lifecycle Surface

Recommended composition:

- Domain cards for overview.
- Dense table for operational state.
- Status badges for lifecycle, health, reachability, and indexing state.
- Primary action: create/start/select domain.
- Secondary action menu for repair/recreate/regenerate/archive/purge preview/purge.
- Confirmation panel for destructive actions.

### Documents Surface

Recommended composition:

- Upload dropzone/card at the top for admins.
- Status cards for current processing jobs.
- Table for document registry.
- Timeline or stepper for ingestion stages.
- Badge mapping for queued, parsing, indexing, completed, and failed.

### Chat And Context Panel Surface

Recommended composition:

- Chat composer with retrieval settings and upload button if applicable.
- Right panel with two tabs: `Context Stream` and `Source Navigation`.
- Evidence cards with source metadata.
- Figure card for extracted images.
- Table card for extracted tables.
- Source detail panel when a workspace-tree source is selected.

## Repo-Specific Defaults

- Use `client/src/components/ui/` only for shadcn primitives.
- Use `client/src/components/surfaces/` for shared surface primitives such as `SectionCard`, `SurfaceHeader`, `StatusChip`, and `PanelState`.
- Keep surface-owned components in the current folders first, such as `client/src/components/settings/` and `client/src/components/chat/`.
- Keep transport and API boundary logic in existing modules under `client/src/api/`, `client/src/lib/api/`, and `client/src/hooks/`.
