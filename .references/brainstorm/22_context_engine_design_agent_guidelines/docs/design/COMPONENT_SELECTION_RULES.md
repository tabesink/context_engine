# Component Selection Rules

## Component research output required

For every UI surface, the shadcn component researcher must produce:

1. Candidate blocks/components.
2. Why each candidate fits the surface.
3. Which existing capability each candidate preserves.
4. Required install commands.
5. Component composition plan.
6. Accessibility notes.
7. Responsive layout notes.
8. Rejected alternatives and why they were rejected.

## Selection heuristics

### Use cards when the user is evaluating objects

Examples:

- Provider cards.
- Domain cards.
- Document processing summaries.
- Figure/table evidence previews.

Card content should include: title, short metadata, status badge, primary action, and secondary action menu.

### Use tables when the user is scanning dense admin state

Examples:

- All providers and model availability.
- Documents and ingestion jobs.
- Domain lifecycle operations.
- Audit-like status records.

Tables should include compact badges and row actions. Avoid turning dense data into oversized cards.

### Use tabs when there are two or three peer views

Examples:

- Context stream vs source navigation in the right panel.
- Provider configuration vs model list vs health/status.
- Domain overview vs documents vs jobs.

Do not use tabs to hide unrelated workflows.

### Use inline panels for primary forms

For major settings forms, use persistent inline panels/cards. Avoid opening a sheet for important configuration if the design intent says the form should remain visible and editable on the page.

### Use dialogs for confirmation, not exploration

Dialogs are appropriate for destructive confirmation and short credential/API-key input when scoped to a selected provider. Do not use dialogs for long multi-section configuration flows.

### Use dropdown menus for secondary row actions

Examples:

- Repair domain.
- Recreate container.
- Archive/delete.
- Purge preview.
- Retry ingestion.

Primary actions should remain visible; dangerous secondary actions should be grouped and confirmed.

## Context Engine surface recommendations

### Providers settings surface

Recommended composition:

- `PageHeader` with title, description, and admin-only status.
- `Tabs` or segmented control for `Providers`, `Models`, and `Health` if the surface is dense.
- Provider cards for high-level provider selection.
- Inline config form for the selected provider.
- Model table for available LLM/embedding models.
- Alert for embedding model immutability after documents are ingested.

### Domain lifecycle surface

Recommended composition:

- Domain cards for overview.
- Dense table for operational state.
- Status badges for lifecycle, health, reachability, and indexing state.
- Primary action: create/start/select domain.
- Secondary action menu for repair/recreate/regenerate/archive/purge preview/purge.
- Confirmation panel for destructive actions.

### Documents surface

Recommended composition:

- Upload dropzone/card at the top for admins.
- Status cards for current processing jobs.
- Table for document registry.
- Timeline or stepper for ingestion stages.
- Badge mapping for queued, parsing, indexing, completed, failed.

### Chat + context panel surface

Recommended composition:

- Chat composer with retrieval settings and upload button if applicable.
- Right panel with two tabs: `Context Stream` and `Source Navigation`.
- Evidence cards with source metadata.
- Figure card for extracted images.
- Table card for extracted tables.
- Source detail panel when a workspace-tree source is selected.

