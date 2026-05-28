# Requirements: LightRAG Domains

## Surface

- Route(s): Settings dialog → `lightrag-domains`
- Users: Admin (full control); non-admin sees disabled nav item
- Surface owner: `settings`

## Current Capabilities To Retain

- [x] List knowledge graph domains with port, document count, embedding model
- [x] Create domain (identity, embedding profile, host port, retrieval defaults)
- [x] Start/stop domain runtime
- [x] Repair, recreate container, regenerate config
- [x] Upload document to domain
- [x] View domain documents (dialog)
- [x] View domain audit logs / event tail (dialog + inline recent events)
- [x] Archive domain (with confirm)
- [x] Preview purge and purge permanently (with confirm)
- [x] Refresh domain and document data
- [x] Live processing status for running domains

## Layout Decisions (locked)

| Topic | Choice |
|-------|--------|
| Layout | Card board — every domain is a bordered card with inline status, actions, events |
| Card expansion | All cards always fully expanded |
| Create form | Toggle via + Create in shell header (hidden by default) |
| Header actions | Refresh + Create in SettingsDialog breadcrumb row |
| Danger zone | Archive / Preview Purge / Purge in per-card More dropdown |
| Managing badge | Removed |
| Events | Compact table (event left, timestamp right) |
| Polling | Poll processing status for all running domains |

## User Roles And Permissions

| Role | Can view | Can edit | Can run actions | Notes |
|---|---:|---:|---:|---|
| Admin | Yes | Yes | Yes | Full surface |
| User | No | No | No | Admin nav disabled |

## Backend/API Dependencies

| Capability | Endpoint/hook/type | Notes |
|---|---|---|
| List domains | `knowledgeGraphAdminApi.list()` | |
| Create domain | `knowledgeGraphAdminApi.create()` | |
| Start/stop/repair | `knowledgeGraphAdminApi.up/down/repair()` | |
| Advanced lifecycle | `recreate`, `regenerate`, `remove`, `purgePreview`, `purge` | |
| Documents | `adminDocumentsApi.list/uploadToDomain` | |
| Audit logs | `adminDocumentsApi.listAuditLogs` | |
| Processing status | `fetchAdminDomainProcessingStatus` via hook | Per running domain |
| Embedding profiles | `aiSettingsApi.get()` | Create form only |

## Required States

- [x] Loading (domains, documents, logs, processing status)
- [x] Empty (no domains)
- [x] Success (notice messages)
- [x] Warning (stale status)
- [x] Error (API failures)
- [x] Disabled (actions while busy, upload when stopped)
- [x] Permission denied (non-admin placeholder)

## Accessibility Requirements

- [x] Keyboard-accessible controls
- [x] Visible focus states (shadcn defaults)
- [x] Status communicated with text labels, not color alone
- [x] Labels for icon-only controls (More menu)

## Responsive Requirements

- [x] Desktop: two-column card body
- [x] Tablet/mobile: stack card columns vertically

## Acceptance Criteria

- [x] All existing lifecycle capabilities preserved
- [x] Refresh and + Create in settings shell header
- [x] Create form toggles via + Create; Cancel hides
- [x] All domains render as bordered cards with two-column bodies
- [x] Running domains show live processing status
- [x] Quick actions per card; More menu includes repair + destructive actions
- [x] Recent events as compact table
- [x] No Manage/Managing/Configured badges

## Non-Goals

- Backend/API contract changes
- Rich lifecycle states from DESIGN.md §8.2
- Type-to-confirm purge
- Polling optimization for large domain counts

## Risks / Open Questions

- Multiple concurrent poll loops scale linearly with running domain count (acceptable for current scale)
