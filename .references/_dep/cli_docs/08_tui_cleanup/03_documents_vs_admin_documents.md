# 3. Documents vs Admin Documents

## 3.1 Why Both Exist Today

The backend has two different document surfaces.

### User document surface

```text
GET /documents
GET /documents/{document_id}
GET /documents/{document_id}/structure
GET /documents/{document_id}/pages/{page_number}
```

Purpose:

- authenticated users browse ready documents
- users inspect document metadata
- users view structure/outline
- users inspect page content

This is the normal document library.

### Admin document surface

```text
GET    /admin/documents
POST   /admin/documents/upload
POST   /admin/documents/{id}/reingest
POST   /admin/documents/{id}/refresh-status
DELETE /admin/documents/{id}
```

Purpose:

- admins upload documents
- admins list all documents, not only ready documents
- admins reingest/refresh-status
- admins delete/soft-delete
- admins see failed/indexing/deleted states

So the backend split is valid.

## 3.2 Why It Feels Redundant in the TUI

The root labels:

```text
Documents
Admin Documents
```

make users ask:

```text
Why are there two document screens?
```

The better root-level concept is one `Documents` area with role-aware actions.

## 3.3 Recommended UI Structure

```text
Documents
  ├── Browse Ready Documents       -> GET /documents
  ├── View Detail                  -> GET /documents/{id}
  ├── View Structure               -> GET /documents/{id}/structure
  ├── View Page                    -> GET /documents/{id}/pages/{page}
  └── Admin Actions                -> admin-only
        ├── Upload                 -> POST /admin/documents/upload
        ├── List All               -> GET /admin/documents
        ├── Reingest               -> POST /admin/documents/{id}/reingest
        ├── Refresh Status         -> POST /admin/documents/{id}/refresh-status
        └── Delete                 -> DELETE /admin/documents/{id}
```

## 3.4 Should Backend Routes Be Merged?

Not now.

Keep existing routes for stability.

Later, optional API simplification could become:

```text
GET /documents?scope=ready
GET /documents?scope=all       # admin-only when scope=all
```

But this is a backend API refactor, not necessary for the TUI cleanup.

## 3.5 Recommended Naming If Kept Separate Temporarily

If you do not fold it immediately, use clearer names:

| Old | Better |
|---|---|
| `Documents` | `Document Library` |
| `Admin Documents` | `Document Admin` |

But the best version is still one `Documents` menu with admin actions nested inside.
