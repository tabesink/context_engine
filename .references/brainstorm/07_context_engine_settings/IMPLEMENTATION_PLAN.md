# Context Engine Settings Modal Implementation Plan

**Prepared for:** junior developer + coding agent  
**Target repo:** `https://github.com/tabesink/context_engine.git`  
**Goal:** Replace the current settings-page navigation with a ChatGPT-style settings popup dialog, retain admin user/account management under an `Account` settings route, and add a `LightRAG` lifecycle-management route inside the same settings dialog.

---

## 1. Executive Summary

The current `context_engine` repository is a FastAPI backend with a Next.js client. The backend already exposes LightRAG lifecycle endpoints under `/admin/lightrag/domains` and public/user domain listing under `/lightrag/domains`. The client already has a full page at `/settings/users` for admin-style user management, but the desired UX is now a modal settings dialog like the attached ChatGPT settings screenshot.

The recommended implementation is **not** to build many separate pages. Instead, create a reusable `SettingsDialog` shell with an internal left navigation list and route panels:

```text
Settings button
  → opens SettingsDialog
    → left nav
       General
       Account
       LightRAG
       Documents / Storage        optional future
       Observability              optional future
       Security                   optional future
    → right panel content
```

The two required panels are:

1. **Account**  
   Retain the current admin-driven user creation, role modification, write-access toggling, password reset, and delete behavior by extracting the current `/settings/users/page.tsx` content into an `AccountSettingsPanel` component.

2. **LightRAG**  
   Add a `LightRAGSettingsPanel` that calls the existing admin lifecycle endpoints: list, create, start/up, stop/down, recreate, regenerate compose/env, archive/delete, and optionally permanent delete if enabled.

Important backend cleanup should be included before or during the LightRAG UI work:

- Fix the LightRAG settings naming mismatch between `LIGHTRAG_DOMAIN_MANIFEST`, `lightrag_domain_registry`, and `lightrag_domains_manifest`.
- Persist `.data/lightrag` in Compose so domain manifests, generated compose files, env files, and domain storage are not lost between container rebuilds.
- Confirm or implement admin user-management endpoints because the client has a user-management page but the currently reviewed FastAPI route registration does not show a dedicated users router.

---

## 2. Evidence-Based Current Codebase Review

### 2.1 Backend entry point and route registration

`app/main.py` creates the FastAPI app, configures CORS, and includes these route modules:

```python
admin, auth, documents, health, jobs, lightrag, lightrag_admin, retrieve, workspace_tree
```

This means the backend is already organized around route modules and can absorb a small `users` or `account` router without changing the architecture.

Observed routes include:

- `/auth/login`
- `/auth/me`
- `/admin/documents/*`
- `/admin/audit-logs`
- `/admin/query-logs`
- `/lightrag/domains`
- `/lightrag/domains/{domain_id}/graphs`
- `/admin/lightrag/domains`
- `/admin/lightrag/domains/{domain_id}/up`
- `/admin/lightrag/domains/{domain_id}/down`
- `/admin/lightrag/domains/{domain_id}/recreate`
- `/admin/lightrag/domains/{domain_id}/regenerate`
- `/admin/lightrag/domains/{domain_id}` delete

### 2.2 Backend stack

`pyproject.toml` identifies the backend stack as:

- FastAPI
- Uvicorn
- SQLAlchemy 2.x
- PostgreSQL via psycopg
- Redis + RQ
- Alembic
- Pydantic Settings
- python-jose + passlib
- Typer/Rich for CLI/TUI

### 2.3 Frontend stack

`client/package.json` identifies the frontend stack as:

- Next.js 16
- React 19
- TypeScript
- Zustand
- Radix UI primitives
- lucide-react
- Tailwind CSS 4
- Graph visualization libraries: sigma, graphology, react-sigma

### 2.4 Existing settings-related client code

The client already has:

```text
client/src/app/settings/users/page.tsx
```

This page appears to manage:

- user list
- create user dialog
- role dropdown
- write-access switch
- reset password dialog
- delete user alert dialog

This logic should be **retained**, but moved into a reusable settings panel:

```text
client/src/components/settings/panels/AccountSettingsPanel.tsx
```

Then `/settings/users/page.tsx` can either:

- redirect to `/chat?settings=account`, or
- render the same `AccountSettingsPanel` as a full-page fallback.

The fallback route is optional. The main requested UX is the modal popup.

### 2.5 Existing LightRAG lifecycle backend capability

The backend already has a `LightRAGDomainService` that supports:

- `list_domains()`
- `get_domain()`
- `create_domain()`
- `regenerate()`
- `up()`
- `down()`
- `recreate()`
- `remove()`

The admin route module exposes this as HTTP endpoints under `/admin/lightrag/domains`.

### 2.6 Important implementation hazard: settings naming mismatch

Current reviewed files show a likely mismatch:

- `app/core/config.py` defines `lightrag_domain_registry`.
- `.env.example` uses `LIGHTRAG_DOMAIN_MANIFEST`.
- `app/lightrag_deploy/settings.py` references `settings.lightrag_domains_manifest`.

This can break lifecycle UI work because the domain service may fail to construct settings or may read/write a different path than retrieval uses.

Recommended fix:

```python
# app/core/config.py
lightrag_domain_registry: Path = Field(
    default=Path(".data/lightrag/domains.json"),
    validation_alias="LIGHTRAG_DOMAIN_MANIFEST",
)

@property
def lightrag_domains_manifest(self) -> Path:
    # Backward-compatible alias until all references are renamed.
    return self.lightrag_domain_registry
```

Then update `LightRAGDeploySettings.from_app_settings()` to use one canonical field.

### 2.7 Important deployment hazard: LightRAG data persistence

`docker-compose.yml` mounts an `uploads` volume to `/app/.data/uploads`, but the reviewed LightRAG deploy code writes to `.data/lightrag`. That path should also be persisted:

```yaml
volumes:
  - uploads:/app/.data/uploads
  - lightrag-data:/app/.data/lightrag
```

Without this, domain manifests and generated compose/env files may be lost during container replacement.

---

## 3. Target UX

The target settings UI should look and behave like the attached screenshot:

```text
┌─────────────────────────────────────────────────────────────────────┐
│  ×                         General                                  │
│ ┌──────────────────────┐  ┌───────────────────────────────────────┐ │
│ │ ⚙ General            │  │ Secure your account                   │ │
│ │ 👤 Account           │  │ Optional security/info card           │ │
│ │ 🧠 LightRAG          │  └───────────────────────────────────────┘ │
│ │ 📄 Documents         │                                           │
│ │ 📊 Observability     │  Appearance                  System  ˅    │
│ │ 🛡 Security          │  Contrast                    System  ˅    │
│ │                      │  Accent color                Default ˅    │
│ │                      │  Retrieval defaults                      │
│ └──────────────────────┘                                           │
└─────────────────────────────────────────────────────────────────────┘
```

### Modal layout specs

Use a single reusable modal shell:

- `max-width`: `760px` to `840px`
- `height`: `min(720px, calc(100vh - 96px))`
- left nav width: `180px`
- right panel: flexible, scrollable
- rounded corners: `rounded-2xl`
- background: app surface token
- shadow: large but soft
- overlay: subtle dark/blurred backdrop
- close button: top-left, like screenshot
- title centered or aligned to content header
- keyboard: `Esc` closes
- focus: trapped inside dialog

### Routes inside modal

These are **internal modal routes**, not necessarily URL routes:

```ts
type SettingsRoute =
  | "general"
  | "account"
  | "lightrag"
  | "documents"
  | "observability"
  | "security";
```

For phase 1, fully implement:

- `general`
- `account`
- `lightrag`

Render the others as disabled placeholders or omit them until needed.

---

## 4. Recommended Frontend Architecture

### 4.1 New file structure

Create:

```text
client/src/components/settings/
  SettingsDialog.tsx
  SettingsShell.tsx
  settings-routes.ts
  panels/
    GeneralSettingsPanel.tsx
    AccountSettingsPanel.tsx
    LightRAGSettingsPanel.tsx
    DocumentsSettingsPanel.tsx          optional placeholder
    ObservabilitySettingsPanel.tsx      optional placeholder
    SecuritySettingsPanel.tsx           optional placeholder

client/src/stores/settings-dialog-store.ts
client/src/api/admin-lightrag.ts
client/src/api/admin-users.ts           only if existing users API client cannot be reused
client/src/types/lightrag-domain.ts
```

### 4.2 Use Radix Dialog through existing UI primitives

The repo already depends on Radix Dialog. Use the existing `client/src/components/ui/dialog` wrapper if present.

Required behavior:

- Modal opens from settings icon.
- Modal closes on close button, overlay click, or Escape.
- Modal traps focus.
- Modal content has accessible title.
- Left-nav items are buttons, not links, unless using deep-link routing.

### 4.3 Keep implementation simple

Do **not** start with Next.js parallel routes/intercepting routes. They are useful for URL-shareable modals, but they add complexity. Start with a controlled dialog and internal Zustand state.

Optional later enhancement:

```text
/chat?settings=account
/chat?settings=lightrag
```

This gives deep links without requiring parallel/intercepted route complexity.

### 4.4 Settings dialog store

Create:

```ts
// client/src/stores/settings-dialog-store.ts
import { create } from "zustand";

type SettingsRoute = "general" | "account" | "lightrag" | "documents" | "observability" | "security";

type SettingsDialogState = {
  open: boolean;
  route: SettingsRoute;
  openSettings: (route?: SettingsRoute) => void;
  closeSettings: () => void;
  setRoute: (route: SettingsRoute) => void;
};

export const useSettingsDialogStore = create<SettingsDialogState>((set) => ({
  open: false,
  route: "general",
  openSettings: (route = "general") => set({ open: true, route }),
  closeSettings: () => set({ open: false }),
  setRoute: (route) => set({ route }),
}));
```

### 4.5 Settings trigger change

Current `AppPageFrame` imports `Settings` from `lucide-react`. Modify it so the settings button calls `openSettings()` instead of navigating to `/settings/users`.

Likely file:

```text
client/src/components/layout/AppPageFrame.tsx
```

Acceptance criteria:

- Clicking settings opens modal from any authenticated page.
- No full-page route navigation happens.
- User remains on `/chat` while settings is open.

### 4.6 Mount the dialog globally

Mount `SettingsDialog` once near app layout so it can open from any authenticated page.

Likely file:

```text
client/src/app/providers.tsx
```

Example:

```tsx
export function Providers({ children }: { children: React.ReactNode }) {
  const bootstrap = useAuthStore((state) => state.bootstrap);

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  return (
    <>
      <AppLayout>{children}</AppLayout>
      <SettingsDialog />
      <Toaster />
    </>
  );
}
```

Make sure `SettingsDialog` checks auth status so it does not render sensitive admin panels for unauthenticated users.

---

## 5. Account Settings Panel Plan

### 5.1 Preserve current user-management behavior

Extract the logic from:

```text
client/src/app/settings/users/page.tsx
```

into:

```text
client/src/components/settings/panels/AccountSettingsPanel.tsx
```

Keep:

- `usersApi.list()`
- `usersApi.create()`
- `usersApi.update()`
- `usersApi.resetPassword()`
- `usersApi.remove()`
- role select
- write-access switch
- reset password dialog
- delete confirmation dialog

### 5.2 Panel structure

```text
Account
  ├─ Current user card
  │   ├─ username/email
  │   ├─ role
  │   └─ status
  └─ Admin user management
      ├─ Users table
      ├─ New user button
      ├─ Role selector
      ├─ Write access switch
      ├─ Password reset
      └─ Delete user
```

### 5.3 Authorization behavior

- Non-admin users see only their account information.
- Admin users see the full user-management table.
- Never render create/delete/update controls for non-admin users.
- Do not rely only on frontend hiding. Backend endpoints must enforce admin.

### 5.4 Backend user-management gap check

The reviewed backend route registration does not show a dedicated `users.py` route module. If a users API does not exist in the current checkout, implement it.

Recommended backend files:

```text
app/api/routes/users.py
app/schemas/users.py
app/storage/repositories/users.py
migrations/versions/<new>_add_user_admin_fields.py
```

Add to `app/main.py`:

```python
from app.api.routes import users
app.include_router(users.router)
```

Recommended endpoints:

```http
GET    /admin/users
POST   /admin/users
PATCH  /admin/users/{user_id}
POST   /admin/users/{user_id}/reset-password
DELETE /admin/users/{user_id}
POST   /admin/users/mark-visited     optional, if client still needs pending count tracking
GET    /admin/users/pending-count     optional
```

Recommended schemas:

```python
class AdminUserResponse(BaseModel):
    id: str
    username: str
    role: Literal["user", "admin"]
    is_active: bool
    can_write: bool
    has_password: bool
    created_at: datetime | None

class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: Literal["user", "admin"]
    can_write: bool = False

class UpdateUserRequest(BaseModel):
    role: Literal["user", "admin"] | None = None
    can_write: bool | None = None

class ResetPasswordRequest(BaseModel):
    new_password: str
```

### 5.5 Database adjustment

Current `UserRow` has `email`, `password_hash`, `role`, `is_active`, and `created_at`. The client type expects `can_write` and `has_password`. Recommended migration:

```python
op.add_column("users", sa.Column("can_write", sa.Boolean(), nullable=False, server_default=sa.false()))
op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
```

Rules:

- Admin users should always behave as `can_write=true`, even if the DB field is false.
- Prevent deleting or demoting the last active admin.
- Prevent a user from deleting themselves.
- Enforce minimum password length on backend, not only frontend.

---

## 6. LightRAG Settings Panel Plan

### 6.1 What the panel should manage

The `LightRAG` route inside settings should expose the lifecycle already present in the backend service:

```text
LightRAG Lifecycle Management
  ├─ Deployment posture
  │   ├─ enabled / disabled
  │   ├─ compose file path
  │   ├─ deploy root
  │   └─ Docker execution mode
  ├─ Domains
  │   ├─ list
  │   ├─ create
  │   ├─ show details
  │   ├─ start/up
  │   ├─ stop/down
  │   ├─ recreate
  │   ├─ regenerate env/compose
  │   ├─ archive/delete
  │   └─ permanent delete if allowed
  └─ Health/status
      ├─ configured
      ├─ running
      ├─ stopped
      ├─ error
      └─ is_healthy
```

### 6.2 Existing backend endpoints to use

Use the existing endpoints before adding new ones:

```http
GET    /admin/lightrag/domains
POST   /admin/lightrag/domains
GET    /admin/lightrag/domains/{domain_id}
POST   /admin/lightrag/domains/{domain_id}/up
POST   /admin/lightrag/domains/{domain_id}/down
POST   /admin/lightrag/domains/{domain_id}/recreate
POST   /admin/lightrag/domains/{domain_id}/regenerate
DELETE /admin/lightrag/domains/{domain_id}?permanent=false
```

User-visible domain list already exists:

```http
GET /lightrag/domains
```

### 6.3 Add one small status endpoint if needed

The current list endpoint can show `status` and `is_healthy`. If the UI needs deploy settings, add:

```http
GET /admin/lightrag/status
```

Response:

```json
{
  "deploy_enabled": true,
  "deploy_root": ".data/lightrag",
  "domains_root": ".data/lightrag/domains",
  "manifest_path": ".data/lightrag/domains.json",
  "compose_file": ".data/lightrag/docker-compose.lightrag-domains.yml",
  "docker_execution_mode": "host",
  "allow_permanent_delete": false,
  "domain_count": 2
}
```

Do not expose provider API keys.

### 6.4 Frontend API client

Create:

```text
client/src/api/admin-lightrag.ts
```

Types:

```ts
export type LightRAGDomain = {
  id: string;
  display_name: string;
  workspace?: string | null;
  host: string;
  host_port: number;
  container_port: number;
  base_url: string;
  host_base_url: string;
  container_base_url: string;
  container_name: string;
  service_name: string;
  status: string;
  is_default: boolean;
  is_healthy?: boolean | null;
  created_at: string;
  updated_at: string;
};

export type CreateLightRAGDomainPayload = {
  domain_id: string;
  display_name?: string;
  host_port?: number;
  make_default?: boolean;
};

export type LightRAGDomainOperationResult = {
  id: string;
  operation: "up" | "down" | "recreate";
  status: "succeeded" | "failed";
  service_name: string;
  message?: string | null;
};
```

Functions:

```ts
listDomains()
createDomain(payload)
getDomain(domainId)
startDomain(domainId)
stopDomain(domainId)
recreateDomain(domainId)
regenerateDomain(domainId)
removeDomain(domainId, permanent = false)
```

### 6.5 LightRAG panel UI layout

```text
LightRAG
  [Deployment disabled warning if disabled]

  Domains                                           [New domain]
  ┌──────────────────────────────────────────────────────────────┐
  │ manual                  running   healthy    default         │
  │ http://127.0.0.1:9621                                      │
  │ [Stop] [Recreate] [Regenerate] [Archive]                    │
  ├──────────────────────────────────────────────────────────────┤
  │ warranty-manuals        stopped   unavailable               │
  │ http://127.0.0.1:9622                                      │
  │ [Start] [Recreate] [Regenerate] [Archive]                   │
  └──────────────────────────────────────────────────────────────┘
```

### 6.6 Create domain dialog

Fields:

- Domain ID: required, lowercase slug, regex `^[a-z0-9][a-z0-9_-]{1,62}$`
- Display name: optional
- Host port: optional
- Make default: switch

Validation:

- Show backend error if duplicate ID or duplicate port.
- Disable submit while busy.
- Refresh list after create.

### 6.7 Operation behavior

For each lifecycle operation:

- Disable the operation button while request is pending.
- Show success/error toast.
- Refresh domain list after request completes.
- Show command stderr/stdout message only in a collapsible details area.
- Use confirm dialog for delete/archive.
- Permanent delete should be hidden unless backend status says allowed.

---

## 7. General Settings Panel Plan

Start small. Do not invent app settings that do not exist.

Include:

```text
General
  Appearance       System / Light / Dark
  Accent color     Default     placeholder if not wired
  Retrieval defaults
    Mode
    top_k
    chunk_top_k
  Graph display
    Show node labels
    Show legend
    Max graph nodes
```

Use existing Zustand settings store where possible:

```text
client/src/stores/settings.ts
```

The existing store already has:

- `theme`
- graph display settings
- query settings
- retrieval history

Make the General panel a thin wrapper around existing store state.

---

## 8. Backend Implementation Tasks

### Task B1 — Fix LightRAG manifest settings mismatch

**Files likely affected**

```text
app/core/config.py
app/lightrag_deploy/settings.py
.env.example
```

**Steps**

1. Pick one canonical name: `lightrag_domain_registry` in Python, `LIGHTRAG_DOMAIN_MANIFEST` in env for backward compatibility.
2. Add a compatibility property if existing code still expects `lightrag_domains_manifest`.
3. Update `LightRAGDeploySettings.from_app_settings()` to use `settings.lightrag_domain_registry`.
4. Add a unit test that constructs `Settings` with `LIGHTRAG_DOMAIN_MANIFEST=.data/lightrag/domains.json`.

**Acceptance criteria**

- App starts without `AttributeError` from `lightrag_domains_manifest`.
- Deploy service reads/writes the same manifest used by retrieval domain registry.
- `.env.example` remains truthful.

### Task B2 — Persist LightRAG deployment data in Compose

**Files likely affected**

```text
docker-compose.yml
README.md
.env.example
```

**Steps**

1. Add `lightrag-data` volume.
2. Mount it into API and worker containers at `/app/.data/lightrag` if both can touch lifecycle state.
3. Document backup requirements.

**Acceptance criteria**

- Domain manifests survive `docker compose down && docker compose up --build`.
- Generated compose/env files survive image rebuild.

### Task B3 — Confirm or implement admin users API

**Files likely affected**

```text
app/api/routes/users.py
app/schemas/users.py
app/storage/repositories/users.py
app/storage/tables.py
migrations/versions/<revision>_add_user_admin_fields.py
app/main.py
```

**Steps**

1. Verify whether a current users API exists in the actual branch.
2. If absent, implement the endpoints listed in section 5.4.
3. Enforce `require_admin` on all admin user-management operations.
4. Prevent deleting self or last active admin.
5. Add tests.

**Acceptance criteria**

- Existing user-management UI works from inside modal.
- Non-admin users cannot list/create/update/delete users.
- `GET /auth/me` includes enough fields for current-user display.

### Task B4 — Optional: Add LightRAG status endpoint

**Files likely affected**

```text
app/api/routes/lightrag_admin.py
app/lightrag_deploy/settings.py
app/schemas/lightrag_admin.py   optional
```

**Acceptance criteria**

- `GET /admin/lightrag/status` returns deploy posture and non-secret paths/settings.
- API keys are never returned.

---

## 9. Frontend Implementation Tasks

### Task F1 — Create settings dialog shell

**Files likely affected**

```text
client/src/components/settings/SettingsDialog.tsx
client/src/components/settings/SettingsShell.tsx
client/src/components/settings/settings-routes.ts
client/src/stores/settings-dialog-store.ts
client/src/app/providers.tsx
```

**Acceptance criteria**

- Settings button opens dialog.
- Dialog matches attached screenshot layout: left nav, header/title, scrollable right content.
- Dialog is keyboard accessible.
- Dialog closes cleanly.

### Task F2 — Move user-management page into Account panel

**Files likely affected**

```text
client/src/app/settings/users/page.tsx
client/src/components/settings/panels/AccountSettingsPanel.tsx
client/src/api/admin-users.ts or existing users API client
client/src/types/user.ts
```

**Acceptance criteria**

- Account panel renders current account info for all users.
- Admins see user management.
- Current create/update/reset/delete workflows still work.
- Existing `/settings/users` route does not break; it can redirect or use the extracted panel.

### Task F3 — Add LightRAG lifecycle panel

**Files likely affected**

```text
client/src/components/settings/panels/LightRAGSettingsPanel.tsx
client/src/api/admin-lightrag.ts
client/src/types/lightrag-domain.ts
```

**Acceptance criteria**

- Admin can list domains.
- Admin can create domain.
- Admin can start/stop/recreate/regenerate/archive a domain.
- UI shows status, health, host URL, container/service name.
- Non-admin users cannot access lifecycle actions.

### Task F4 — Add General panel

**Files likely affected**

```text
client/src/components/settings/panels/GeneralSettingsPanel.tsx
client/src/stores/settings.ts
```

**Acceptance criteria**

- Theme selector updates persisted theme state.
- Existing graph/retrieval options are shown only if they are already backed by the store.
- No fake settings are introduced.

### Task F5 — Replace settings button navigation

**Files likely affected**

```text
client/src/components/layout/AppPageFrame.tsx
```

**Acceptance criteria**

- Clicking settings opens the modal.
- It does not navigate away from `/chat`.
- Logout and login behavior remain unchanged.

---

## 10. Suggested Component Skeleton

```tsx
// client/src/components/settings/SettingsDialog.tsx
"use client";

import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { useSettingsDialogStore } from "@/stores/settings-dialog-store";
import { SettingsShell } from "./SettingsShell";

export function SettingsDialog() {
  const open = useSettingsDialogStore((s) => s.open);
  const closeSettings = useSettingsDialogStore((s) => s.closeSettings);

  return (
    <Dialog open={open} onOpenChange={(next) => !next && closeSettings()}>
      <DialogContent className="max-w-[820px] p-0 overflow-hidden rounded-2xl">
        <DialogTitle className="sr-only">Settings</DialogTitle>
        <SettingsShell />
      </DialogContent>
    </Dialog>
  );
}
```

```tsx
// client/src/components/settings/SettingsShell.tsx
"use client";

import { Settings, UserRound, BrainCircuit, Database, Shield, BarChart3 } from "lucide-react";
import { useSettingsDialogStore } from "@/stores/settings-dialog-store";
import { GeneralSettingsPanel } from "./panels/GeneralSettingsPanel";
import { AccountSettingsPanel } from "./panels/AccountSettingsPanel";
import { LightRAGSettingsPanel } from "./panels/LightRAGSettingsPanel";

const routes = [
  { id: "general", label: "General", icon: Settings },
  { id: "account", label: "Account", icon: UserRound },
  { id: "lightrag", label: "LightRAG", icon: BrainCircuit },
  { id: "documents", label: "Documents", icon: Database, disabled: true },
  { id: "observability", label: "Observability", icon: BarChart3, disabled: true },
  { id: "security", label: "Security", icon: Shield, disabled: true },
] as const;

export function SettingsShell() {
  const route = useSettingsDialogStore((s) => s.route);
  const setRoute = useSettingsDialogStore((s) => s.setRoute);

  return (
    <div className="flex h-[min(720px,calc(100vh-96px))] bg-[var(--background)] text-[var(--foreground)]">
      <aside className="w-48 shrink-0 border-r border-[var(--border)] p-3">
        {routes.map((item) => (
          <button
            key={item.id}
            disabled={item.disabled}
            onClick={() => setRoute(item.id)}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm disabled:opacity-40 data-[active=true]:bg-[var(--muted)]"
            data-active={route === item.id}
          >
            <item.icon className="size-4" />
            {item.label}
          </button>
        ))}
      </aside>

      <main className="min-w-0 flex-1 overflow-y-auto p-5">
        {route === "general" && <GeneralSettingsPanel />}
        {route === "account" && <AccountSettingsPanel />}
        {route === "lightrag" && <LightRAGSettingsPanel />}
      </main>
    </div>
  );
}
```

---

## 11. Testing Plan

### Backend tests

Add or update pytest coverage for:

```text
tests/api/test_admin_users.py
tests/api/test_lightrag_admin_routes.py
tests/lightrag_deploy/test_settings.py
tests/lightrag_deploy/test_domain_service.py
```

Minimum tests:

- non-admin cannot access `/admin/users`
- admin can create user
- admin can update role
- admin can reset password
- admin cannot delete self
- admin cannot delete last active admin
- LightRAG deploy disabled returns clear error
- LightRAG create rejects duplicate ID
- LightRAG start/stop/recreate call runner with expected service name
- settings alias loads `LIGHTRAG_DOMAIN_MANIFEST`

### Frontend tests / checks

At minimum:

```bash
cd client
npm run lint
npm run build
```

Manual UI checks:

- Settings button opens modal on `/chat`.
- Escape closes modal.
- Account tab loads user list for admin.
- Non-admin sees no admin-only controls.
- LightRAG tab loads domain list.
- Domain operation buttons refresh status.
- Errors show cleanly.

---

## 12. Implementation Order

Recommended sequence:

```text
Phase 0 — Confirm branch and run baseline
  - python -m pytest -q
  - cd client && npm run lint && npm run build

Phase 1 — Backend safety fixes
  - fix LightRAG manifest settings mismatch
  - persist .data/lightrag volume
  - confirm or implement admin users API

Phase 2 — Settings modal shell
  - create dialog store
  - create SettingsDialog and SettingsShell
  - mount globally in Providers
  - wire settings button

Phase 3 — Account panel migration
  - extract settings/users page logic
  - retain full user management
  - keep page fallback/redirect

Phase 4 — LightRAG lifecycle panel
  - create API client
  - create list/create/actions UI
  - add status endpoint only if needed

Phase 5 — Polish and tests
  - responsive layout
  - loading/error states
  - accessibility checks
  - backend + frontend tests
```

---

## 13. Definition of Done

The feature is complete when:

1. Clicking the settings button opens a popup dialog styled like the attached screenshot.
2. The modal has a left-hand settings nav.
3. `Account` contains current user info and retains admin user creation/modification/deletion capability.
4. `LightRAG` contains full lifecycle management for domains.
5. Non-admin users cannot access admin-only actions.
6. LightRAG lifecycle actions use existing backend service boundaries; no duplicate lifecycle logic is added in the frontend.
7. LightRAG manifest/config naming is consistent.
8. LightRAG deployment state is persisted in Compose.
9. Backend tests pass.
10. Frontend lint/build pass.
11. The old `/settings/users` route does not become a broken route.

---

## 14. Coding Agent Prompt

Use this prompt with a coding agent:

```md
You are working in https://github.com/tabesink/context_engine.git.

Implement a ChatGPT-style settings popup dialog for the Next.js client. When an authenticated user clicks the settings button, open a modal dialog with a left navigation panel and right content panel. Do not navigate away from `/chat`.

Required settings routes inside the modal:

1. General
2. Account
3. LightRAG

Account route:
- Retain existing admin user-management behavior currently located at `client/src/app/settings/users/page.tsx`.
- Extract it into `client/src/components/settings/panels/AccountSettingsPanel.tsx`.
- Non-admin users should only see their own account info.
- Admins should see user list, create user, role update, write-access toggle, reset password, and delete controls.

LightRAG route:
- Add `client/src/components/settings/panels/LightRAGSettingsPanel.tsx`.
- Use existing backend endpoints under `/admin/lightrag/domains` for lifecycle actions.
- Implement list, create, start/up, stop/down, recreate, regenerate, archive/delete, and refresh.
- Hide lifecycle controls from non-admin users.

Backend cleanup:
- Fix the LightRAG manifest settings mismatch: `LIGHTRAG_DOMAIN_MANIFEST`, `lightrag_domain_registry`, and `lightrag_domains_manifest` must resolve to one canonical manifest path.
- Persist `.data/lightrag` in Docker Compose with a named volume.
- Verify whether admin user-management API endpoints exist. If absent, implement a small `app/api/routes/users.py` router and include it in `app/main.py`.

Architecture rules:
- Keep the modal shell reusable.
- Keep API calls in API client modules, not directly in UI components.
- Do not duplicate backend LightRAG lifecycle logic in the frontend.
- Do not expose provider API keys in UI or status endpoints.
- Prefer controlled Radix Dialog over Next.js parallel/intercepting routes for phase 1.
- Add tests for backend auth boundaries and LightRAG settings alias.
- Run `python -m pytest -q`, `cd client && npm run lint`, and `cd client && npm run build` before completion.
```
