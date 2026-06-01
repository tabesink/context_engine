# 06 — Frontend Wiring Plan

## Target Frontend Principle

```text
Components render UI.
Stores hold local/session state.
API clients call backend endpoints.
No scattered raw fetch calls inside components.
```

## Recommended API Modules

```text
client/src/lib/api/auth.ts
client/src/lib/api/documents.ts
client/src/lib/api/admin-documents.ts
client/src/lib/api/retrieve.ts
client/src/lib/api/domains.ts
client/src/lib/api/operations.ts
client/src/lib/api/provider.ts
client/src/lib/api/users.ts
```

## Recommended Stores

```text
client/src/stores/auth-store.ts
  auth/session/token/current user

client/src/stores/lightrag-domain-store.ts
  selected domain only

client/src/stores/chat-session-store.ts
  chat messages/session state

client/src/stores/settings-dialog-store.ts
  UI open/close/nav state only
```

## Route/Page Recommendations

```text
/chat
  Ask/retrieve interface

/documents
  Uploaded documents list

/documents/[id]
  Document viewer/source navigation/assets/chunks

/settings/domains
  Domain lifecycle management

/settings/provider
  Provider diagnostics/config display

/settings/users
  User/admin management

/operations
  Global async activity visibility
```

## Domain Card UI Actions

Keep:

```text
Start
Stop
Delete
```

Remove from domain More menu:

```text
Upload document
View documents
View logs
Repair
Recreate
Regenerate
Purge
```

Reason: document upload and viewing deserve dedicated document routes, not hidden lifecycle-menu actions.

## Upload UI Wiring

Upload flow:

```text
Upload form
  │
  ▼
adminDocumentsApi.upload(file, domainId)
  │
  ▼
returns document_id + operation_id + processing_status_url
  │
  ▼
poll documentsApi.getProcessingStatus(document_id)
  │
  ▼
show status stage labels
```

## Operations UI Wiring

Operations flow:

```text
Operations page
  │
  ▼
operationsApi.list()
  │
  ▼
render table of global activity
  │
  ├─ filter by type
  ├─ filter by status
  └─ click operation for details
```

## Chat/Retrieval UI Wiring

```text
Chat composer
  │
  ├─ selected domain from lightrag-domain-store
  └─ query text
        │
        ▼
retrieveApi.retrieve({ query, domain_id })
        │
        ▼
render answer/evidence/source map/assets
```

## Frontend Cleanup Search Commands

```bash
grep -R "ingestion-status" client/src

grep -R "\/jobs" client/src

grep -R "admin/lightrag" client/src

grep -R "fetch(" client/src
```

## Acceptance Criteria

- Components do not hardcode deprecated endpoints.
- Domain More menu contains only lifecycle actions.
- Upload and document viewing have their own UI surfaces.
- Operations page is the global visibility layer for async work.
