# Phase 1 — Settings Shell and Navigation Preparation

## Goal

Create or refine a stable settings/admin shell that can host future Context Engine surfaces without reworking layout later.

This phase prepares the broad UI change.

## Target navigation

```txt
Settings
├── Account
├── Provider
├── LightRAG Domains
├── Documents
├── Jobs
└── System
```

Admin-only entries:

- Provider
- LightRAG Domains
- Documents
- Jobs
- System, if it contains admin operations

Non-admin users should not see admin-only management routes.

## Scope

Allowed:

- Add left-nav settings shell if missing.
- Preserve existing account/user management.
- Add placeholder panels for future phases.
- Wire route/tab state cleanly.
- Add access-control guards for admin-only nav items.

Not allowed:

- Implementing domain lifecycle logic.
- Implementing document processing status.
- Implementing job queue UI.
- Adding new backend status routes.

## Suggested files

Inspect first; adapt paths to current app structure.

```txt
client/src/components/settings/SettingsDialog.tsx
client/src/components/settings/SettingsShell.tsx
client/src/components/settings/SettingsNav.tsx
client/src/components/settings/routes/AccountSettings.tsx
client/src/components/settings/routes/ProviderSettings.tsx
client/src/components/settings/routes/LightRagDomainsSettings.tsx
client/src/components/settings/routes/DocumentsSettings.tsx
client/src/components/settings/routes/JobsSettings.tsx
client/src/components/settings/routes/SystemSettings.tsx
```

If settings components already exist, extend them instead of creating duplicates.

## Backend/API wiring

No new backend routes. Use existing auth/user state to determine admin visibility.

Confirm existing frontend auth shape:

```bash
rg -n "isAdmin|role|admin|currentUser|useAuth|auth" client/src
```

## UI guidance

Use shadcn Settings + Sidebar/Dialog patterns:

- fixed left nav
- right content panel
- compact route headers
- no shadows
- no heavy background blocks
- active route as subtle filled pill

## Acceptance criteria

- Settings shell supports route switching.
- Existing account functionality remains intact.
- Admin-only entries are hidden or disabled for non-admins.
- Placeholder pages clearly state “not wired yet” and do not fake data.
- No direct LightRAG calls are added.

## Validation

```bash
cd client
npm run lint
npm run build
```

## Human inspection gate

Inspect the shell visually before adding real domain/document/jobs logic.

Questions:

- Does the shell feel like the future home for admin surfaces?
- Is it compact enough?
- Are admin-only nav items correctly gated?
- Did the phase avoid backend/status complexity?


## shadcn references for this phase

- Sidebar primitive: https://ui.shadcn.com/docs/components/sidebar
- Dialog primitive: https://ui.shadcn.com/docs/components/dialog
- Tabs primitive: https://ui.shadcn.com/docs/components/tabs
- Settings block category: https://www.shadcn.io/blocks/settings
- Sidebar block category: https://www.shadcn.io/blocks/sidebar

Also open `reference/SHADCN_BLOCK_LINKS.md` before implementation.
