# shadcn Block and Component Link Registry

Use these links as **reference patterns**, not as wholesale imports. The coding agent should inspect the block layout, then rebuild the needed UI with Context Engine's existing component system and `DESIGN.md` rules.

## shadcn.io block catalog

- Main blocks catalog: https://www.shadcn.io/blocks
- Cursor MCP setup: https://www.shadcn.io/mcp/cursor

## Recommended block references for Context Engine

| Context Engine surface | Primary shadcn block reference | Use it for | Do not copy blindly |
|---|---|---|---|
| Admin LightRAG domain health overview | Dashboard Platform Overview — https://www.shadcn.io/blocks/dashboard-platform-overview | Compact top-level metrics, status dots, stale/healthy/error summary | Large decorative charts or marketing-style stats |
| Per-domain Docker/runtime health | Monitoring Container Status — https://www.shadcn.io/blocks/monitoring-container-status | Container state, health probe, port, service status, last checked | CPU/memory graphs unless backend actually exposes metrics |
| Domain lifecycle operation clarity | CRUD Status Workflow — https://www.shadcn.io/blocks/crud-status-workflow | Controlled state machine: start/stop/repair/archive/purge, allowed next actions | Showing every backend verb as a top-level button |
| Document ingestion/processing status | Dashboard PDF Processing — https://www.shadcn.io/blocks/dashboard-pdf-processing | Upload → parse → chunk → embed → graph/index → indexed/failed | OCR-specific copy unless relevant |
| Background jobs | Dashboard Job Queue — https://www.shadcn.io/blocks/dashboard-job-queue | Queued/running/failed/completed jobs, retry count, worker status | Time-series queue charts unless implemented |
| LightRAG deployment/provider configuration | Settings Deployment Config — https://www.shadcn.io/blocks/settings-deployment-config | Domain config, provider/model profile, deployment toggles | CI/CD terminology that does not map to Context Engine |
| Archive/purge/destructive actions | Settings Danger Zone — https://www.shadcn.io/blocks/settings-danger-zone | Archive, purge preview, typed confirmation, permanent purge | Plain delete buttons in normal action rows |
| Admin roles/permissions, if exposed | CRUD Access Control — https://www.shadcn.io/blocks/crud-access-control | Role/resource matrix, admin-only visibility, permission hints | A full permission matrix if Context Engine only needs simple admin/user separation |

## Category links for additional candidates

- Dashboard blocks: https://www.shadcn.io/blocks/dashboard
- CRUD blocks: https://www.shadcn.io/blocks/crud
- Monitoring blocks: https://www.shadcn.io/blocks/monitoring
- Settings blocks: https://www.shadcn.io/blocks/settings
- Tables blocks: https://www.shadcn.io/blocks/tables
- Sidebar blocks: https://www.shadcn.io/blocks/sidebar
- Stats blocks: https://www.shadcn.io/blocks/stats
- Stepper blocks: https://www.shadcn.io/blocks/stepper
- Timeline blocks: https://www.shadcn.io/blocks/timeline
- Empty State blocks: https://www.shadcn.io/blocks/empty-state
- Error blocks: https://www.shadcn.io/blocks/error
- Skeleton blocks: https://www.shadcn.io/blocks/skeleton
- File Upload blocks: https://www.shadcn.io/blocks/file-upload

## shadcn/ui primitive component docs

Use official `ui.shadcn.com` primitives for implementation. Prefer existing project-local primitives if already installed.

| Primitive | Link | Context Engine use |
|---|---|---|
| Button | https://ui.shadcn.com/docs/components/button | Start/stop/repair/archive actions; use pill style for interactive elements |
| Card | https://ui.shadcn.com/docs/components/card | Domain overview cards, status cards, document cards |
| Dialog | https://ui.shadcn.com/docs/components/dialog | Settings shell and confirmations that are not destructive |
| Alert Dialog | https://ui.shadcn.com/docs/components/alert-dialog | Purge confirmation, destructive warnings |
| Sidebar | https://ui.shadcn.com/docs/components/sidebar | Settings left navigation if not already present |
| Tabs | https://ui.shadcn.com/docs/components/tabs | Settings subroutes; right-panel Context Stream / Source Navigator if needed |
| Table | https://ui.shadcn.com/docs/components/table | Domain registry, document status table, job queue table |
| Badge | https://ui.shadcn.com/docs/components/badge | Status chips: running, stopped, failed, processing, indexed, stale |
| Alert | https://ui.shadcn.com/docs/components/alert | Warnings, stale backend status, LightRAG unreachable notices |
| Progress | https://ui.shadcn.com/docs/components/progress | Processing progress when backend returns progress_ratio |
| Skeleton | https://ui.shadcn.com/docs/components/skeleton | Loading states for status cards/tables |
| Dropdown Menu | https://ui.shadcn.com/docs/components/dropdown-menu | Advanced actions: recreate/regenerate/debug-only actions |
| Tooltip | https://ui.shadcn.com/docs/components/tooltip | Clarify repair/recreate/regenerate semantics without clutter |
| Separator | https://ui.shadcn.com/docs/components/separator | Flat section boundaries in settings panels |
| Scroll Area | https://ui.shadcn.com/docs/components/scroll-area | Settings route content, right panel content, event tail |

## Installation guidance for coding agents

First inspect existing local components before installing anything:

```bash
find client/src/components/ui -maxdepth 1 -type f | sort
rg -n "from ['\"]@/components/ui/(button|card|dialog|sidebar|tabs|table|badge|alert|progress|skeleton)" client/src
```

Only install missing primitives that are needed for the current phase. Example commands:

```bash
cd client
pnpm dlx shadcn@latest add button card badge table tabs skeleton alert progress
pnpm dlx shadcn@latest add alert-dialog dropdown-menu tooltip separator scroll-area
```

If using shadcn.io Pro/MCP in Cursor, follow the Cursor MCP setup link above. Do not commit personal tokens. If a team config is used, commit only a placeholder such as `${SHADCNIO_TOKEN}` and load the token from a local environment variable.

## Context Engine adaptation rules

- Use blocks as structural references only.
- Keep Context Engine's flat grayscale style.
- Avoid shadows, gradients, oversized icons, and decorative color.
- Use `rounded-xl` for non-interactive cards and `rounded-full` for buttons/chips.
- Use muted borders and compact typography.
- Do not add charts unless backend exposes real metrics.
- Do not wire UI directly to LightRAG. All data must come through Context Engine API clients.
