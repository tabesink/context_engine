# shadcn Block Mapping for Context Engine Surfaces

Use shadcn blocks as layout/interaction references, not as wholesale visual imports. Adapt everything to Context Engine's restrained design system.

## Recommended block categories

| Context Engine need | shadcn category/pattern | Adaptation notes |
|---|---|---|
| Admin route shell | Settings + Sidebar + Dialog | Left nav with route-like panels. Keep current account settings. |
| Domain health overview | Dashboard + Stats | Compact 2x2 or 4-card metrics: active domains, processing docs, failed docs, stale domains. |
| Domain runtime status | Monitoring / Container Status | Container state, health probe, port, last checked. No heavy charts initially. |
| Lifecycle operation clarity | CRUD Status Workflow / Stepper | Show current state, allowed next actions, blocked actions. |
| Document ingestion status | Dashboard PDF Processing / File Upload | Upload → parse → chunk → embed → graph/index → ready/failed. |
| Jobs | Dashboard Job Queue / Tables | queued/running/failed/completed, retry action. |
| Destructive operations | Settings Danger Zone | Archive, preview purge, purge confirm. Type-to-confirm for purge. |
| Event history | Timeline / Activity Feed | Domain events: created, started, repaired, failed, archived, purged. |
| Empty/error/loading states | Empty State, Error, Skeleton | Reusable compact panel states. |


## Direct block links

Use `reference/SHADCN_BLOCK_LINKS.md` as the canonical link registry. Key links:

| Pattern | Direct link |
|---|---|
| Dashboard Platform Overview | https://www.shadcn.io/blocks/dashboard-platform-overview |
| Monitoring Container Status | https://www.shadcn.io/blocks/monitoring-container-status |
| CRUD Status Workflow | https://www.shadcn.io/blocks/crud-status-workflow |
| Dashboard PDF Processing | https://www.shadcn.io/blocks/dashboard-pdf-processing |
| Dashboard Job Queue | https://www.shadcn.io/blocks/dashboard-job-queue |
| Settings Deployment Config | https://www.shadcn.io/blocks/settings-deployment-config |
| Settings Danger Zone | https://www.shadcn.io/blocks/settings-danger-zone |
| CRUD Access Control | https://www.shadcn.io/blocks/crud-access-control |

## Primitive component docs

Use official shadcn/ui primitive docs when implementing local components:

- Button: https://ui.shadcn.com/docs/components/button
- Card: https://ui.shadcn.com/docs/components/card
- Dialog: https://ui.shadcn.com/docs/components/dialog
- Sidebar: https://ui.shadcn.com/docs/components/sidebar
- Tabs: https://ui.shadcn.com/docs/components/tabs
- Table: https://ui.shadcn.com/docs/components/table
- Badge: https://ui.shadcn.com/docs/components/badge
- Alert Dialog: https://ui.shadcn.com/docs/components/alert-dialog
- Dropdown Menu: https://ui.shadcn.com/docs/components/dropdown-menu
- Progress: https://ui.shadcn.com/docs/components/progress
- Skeleton: https://ui.shadcn.com/docs/components/skeleton

## Blocks to avoid or defer

- Kanban: lifecycle is a state machine, not manually moved task cards.
- Large analytics charts: defer until actual time-series metrics exist.
- Marketing/hero blocks: not appropriate for admin surfaces.
- Heavy animated blocks: likely violates low-noise design.

## Styling rules

- Prefer `border`, `bg-background`, `bg-muted/30`, `text-muted-foreground`.
- Avoid `shadow`, gradients, oversized icons, and decorative color.
- Use `rounded-xl` for cards and `rounded-full` for buttons/chips.
- Keep density compact: small headers, 12–14px metadata, table rows with minimal height.
