# CLI API Surface ASCII Screens

Repository reviewed: `tabesink/context_engine`  
Document target path: `docs/CLI_API_SURFACE_ASCII_SCREENS.md`  
Generated: 2026-05-16

---

## 0. Purpose

This document maps the `ragcli` command-line interface and its lightweight interactive TUI screens to the backend API surfaces in the `context_engine` repository.

It is written for junior developers who need to understand:

- what the CLI can call today;
- which backend routes each screen or command uses;
- which API surfaces are admin-only;
- which CLI surfaces are planned stubs and not yet backed by API routes;
- what the interactive terminal screens should look like in ASCII.

This is not a redesign. It documents the current CLI/API shape and gives lightweight recommendations for keeping the CLI useful as a backend/API testing tool and future frontend reference.

---

## 1. Source Files Reviewed

```text
+----+-----------------------------------------+----------------------------------------------+
| #  | Source file                             | Why it matters                               |
+----+-----------------------------------------+----------------------------------------------+
| 01 | README.md                               | Confirms app purpose and ragcli entry point  |
| 02 | cli/main.py                             | Typer command tree and API calls             |
| 03 | cli/tui/app.py                          | Interactive TUI runtime                      |
| 04 | cli/tui/screens/login.py                | TUI login and logout screens                 |
| 05 | cli/tui/screens/main_menu.py            | Authenticated TUI main menu                  |
| 06 | cli/tui/screens/content.py              | TUI domain screens and API calls             |
| 07 | cli/screens/session.py                  | Auth/session render builders                 |
| 08 | cli/screens/documents.py                | Document screen builders                     |
| 09 | cli/screens/admin_documents.py          | Admin document screen builders               |
| 10 | cli/screens/retrieval.py                | Retrieval and answer screen builders         |
| 11 | cli/screens/jobs.py                     | Job screen builders                          |
| 12 | cli/screens/lightrag.py                 | LightRAG label/graph screen builders         |
| 13 | cli/screens/observability.py            | Audit/query log screen builders              |
| 14 | cli/screens/planned.py                  | Planned unsupported CLI/API gaps             |
| 15 | app/main.py                             | Backend router registration                  |
| 16 | app/api/routes/auth.py                  | Auth API routes                              |
| 17 | app/api/routes/documents.py             | User document API routes                     |
| 18 | app/api/routes/admin.py                 | Admin API routes                             |
| 19 | app/api/routes/query.py                 | Retrieval/answer API routes                  |
| 20 | app/api/routes/lightrag.py              | LightRAG proxy API routes                    |
| 21 | app/api/routes/jobs.py                  | Indexing job API routes                      |
| 22 | app/api/routes/health.py                | Health/readiness API routes                  |
+----+-----------------------------------------+----------------------------------------------+
```

---

## 2. CLI / API Surface Index

```text
+----+---------------------------+------------------------------------+------------------------------------------------------+----------------+
| #  | CLI Surface               | Purpose                            | API Routes Used                                      | Access Level   |
+----+---------------------------+------------------------------------+------------------------------------------------------+----------------+
| 01 | ragcli login              | Authenticate and store token       | POST /auth/login                                     | Public         |
| 02 | ragcli logout             | Clear local stored token           | None                                                 | Local only     |
| 03 | ragcli auth me            | Show current authenticated user    | GET /auth/me                                         | User/Admin     |
| 04 | ragcli ui                 | Launch interactive TUI             | Multiple, based on selected screen                   | User/Admin     |
| 05 | ragcli documents list     | List ready documents               | GET /documents                                       | User/Admin     |
| 06 | ragcli documents show     | Show document metadata             | GET /documents/{document_id}                         | User/Admin     |
| 07 | ragcli documents structure| Show navigation/structure tree     | GET /documents/{document_id}/structure               | User/Admin     |
| 08 | ragcli documents page     | Show parsed page text              | GET /documents/{document_id}/pages/{page_number}     | User/Admin     |
| 09 | ragcli documents retrieve | Retrieve context/evidence          | POST /query/retrieve                                 | User/Admin     |
| 10 | ragcli documents answer   | Generate answer with sources       | POST /query/answer                                   | User/Admin     |
| 11 | ragcli query              | Shortcut answer command            | POST /query                                          | User/Admin     |
| 12 | ragcli retrieval compare  | Compare retrieval modes            | POST /query/retrieve, repeated by mode               | User/Admin     |
| 13 | ragcli admin dashboard    | Load admin summary                 | GET /admin/documents, /jobs, /admin/*logs            | Admin          |
| 14 | ragcli admin documents list| List all documents                | GET /admin/documents                                 | Admin          |
| 15 | ragcli admin documents upload| Upload document                  | POST /admin/documents/upload                         | Admin          |
| 16 | ragcli admin documents upload-flow| Upload and show job status   | POST /admin/documents/upload, GET /jobs/{job_id}     | Admin          |
| 17 | ragcli admin documents index| Queue indexing job               | POST /admin/documents/{document_id}/index            | Admin          |
| 18 | ragcli admin documents reindex| Queue reindexing job           | POST /admin/documents/{document_id}/reindex          | Admin          |
| 19 | ragcli admin documents delete| Soft-delete document            | DELETE /admin/documents/{document_id}                | Admin          |
| 20 | ragcli admin audit-logs list| View audit logs                  | GET /admin/audit-logs                                | Admin          |
| 21 | ragcli admin query-logs list| View query logs                  | GET /admin/query-logs                                | Admin          |
| 22 | ragcli jobs list          | List indexing jobs                 | GET /jobs                                            | Admin          |
| 23 | ragcli jobs status        | Show one job                       | GET /jobs/{job_id}                                   | Admin          |
| 24 | ragcli jobs retry         | Retry failed job                   | POST /jobs/{job_id}/retry                            | Admin          |
| 25 | ragcli lightrag labels list| List graph labels                 | GET /graph/label/list                                | User/Admin     |
| 26 | ragcli lightrag labels popular| Popular graph labels           | GET /graph/label/popular?limit=                      | User/Admin     |
| 27 | ragcli lightrag labels search| Search graph labels             | GET /graph/label/search?q=&limit=                    | User/Admin     |
| 28 | ragcli lightrag graphs show| Show graph by label               | GET /graphs?label=&max_depth=&max_nodes=             | User/Admin     |
| 29 | ragcli screen documents   | Human screen alias                 | GET /documents                                       | User/Admin     |
| 30 | ragcli screen retrieval   | Human screen alias                 | POST /query/retrieve                                 | User/Admin     |
| 31 | ragcli screen graph       | Human screen alias                 | GET /graphs?label=&max_depth=2&max_nodes=100         | User/Admin     |
| 32 | ragcli screen admin       | Human admin dashboard alias        | GET /admin/documents, /jobs, /admin/*logs            | Admin          |
| 33 | ragcli screen gaps        | Show planned unsupported surfaces  | None                                                 | Local only     |
| 34 | planned stubs             | Future users/agents/chat/runs/etc. | None; returns not_supported_by_backend               | Not supported  |
+----+---------------------------+------------------------------------+------------------------------------------------------+----------------+
```

---

## 3. Backend API Coverage Matrix

```text
+----+-----------------------------------------------+-------------------------------+-------------------+-------------------------------+
| #  | Backend API Route                             | CLI Coverage                  | TUI Coverage      | Recommendation                |
+----+-----------------------------------------------+-------------------------------+-------------------+-------------------------------+
| 01 | GET /health                                   | Missing                       | Missing           | Add ragcli health             |
| 02 | GET /health/readiness                         | Missing                       | Missing           | Add ragcli health readiness   |
| 03 | POST /auth/login                              | Covered: ragcli login         | Covered           | Keep                          |
| 04 | GET /auth/me                                  | Covered: ragcli auth me       | Covered at startup| Keep                          |
| 05 | GET /documents                                | Covered                       | Covered           | Keep                          |
| 06 | GET /documents/{document_id}                  | Covered                       | Covered           | Keep                          |
| 07 | GET /documents/{document_id}/structure        | Covered                       | Missing direct UI | Add detail action if needed   |
| 08 | GET /documents/{document_id}/pages/{page}     | Covered                       | Missing direct UI | Add detail action if needed   |
| 09 | POST /query/retrieve                          | Covered                       | Covered           | Keep                          |
| 10 | POST /query/answer                            | Covered                       | Covered           | Keep                          |
| 11 | POST /query                                   | Covered                       | Not direct        | Keep shortcut command         |
| 12 | GET /admin/ping                               | Missing                       | Missing           | Add admin ping command        |
| 13 | GET /admin/documents                          | Covered                       | Covered           | Keep                          |
| 14 | POST /admin/documents/upload                  | Covered                       | Covered           | Keep; improve path UX         |
| 15 | POST /admin/documents/{id}/index              | Covered                       | Partial           | Add selectable TUI action     |
| 16 | POST /admin/documents/{id}/reindex            | Covered                       | Partial           | Add selectable TUI action     |
| 17 | DELETE /admin/documents/{id}                  | Covered                       | Partial           | Add confirmation screen       |
| 18 | GET /admin/audit-logs                         | Covered                       | Covered           | Keep                          |
| 19 | GET /admin/query-logs                         | Covered                       | Covered           | Keep                          |
| 20 | GET /jobs                                     | Covered                       | Covered           | Keep                          |
| 21 | GET /jobs/{job_id}                            | Covered                       | Covered via upload| Keep                          |
| 22 | POST /jobs/{job_id}/retry                     | Covered                       | Partial           | Add selectable TUI action     |
| 23 | GET /graphs                                   | Covered                       | Alias/partial     | Add graph prompt screen       |
| 24 | GET /graph/label/list                         | Covered                       | Not direct        | Add labels menu option        |
| 25 | GET /graph/label/popular                      | Covered                       | Covered           | Keep                          |
| 26 | GET /graph/label/search                       | Covered                       | Missing direct UI | Add label search screen       |
+----+-----------------------------------------------+-------------------------------+-------------------+-------------------------------+
```

---

## 4. TUI Navigation Model

The interactive mode starts with:

```bash
ragcli ui
```

Current authenticated main menu items:

```text
+----+-------------------+-----------------------------------------+
| #  | Menu Item         | Screen / API group                      |
+----+-------------------+-----------------------------------------+
| 01 | Documents         | Document library and document detail    |
| 02 | Retrieval         | Query context retrieval and answers     |
| 03 | LightRAG Graphs   | Popular labels / graph discovery        |
| 04 | Admin Documents   | Admin document list                     |
| 05 | Jobs              | Indexing jobs                           |
| 06 | Observability     | Query logs and audit logs               |
| 07 | Backend Gaps      | Planned unsupported CLI/API surfaces    |
| 08 | Logout            | Clear local session                     |
| 09 | Quit              | Exit TUI                                |
+----+-------------------+-----------------------------------------+
```

Common controls:

```text
+----------------+-----------------------------------------+
| Key            | Meaning                                 |
+----------------+-----------------------------------------+
| Up / Down      | Move selected row or option             |
| Enter          | Open selected item or submit form       |
| B              | Back                                    |
| Q              | Quit                                    |
| Ctrl+R         | Refresh current API-backed screen       |
| U              | Upload document from Documents screen   |
| M              | Cycle retrieval mode                    |
| K              | Increase retrieval Top K                |
| Tab            | Switch active form field                |
+----------------+-----------------------------------------+
```

---

# 5. ASCII Screens by API Surface

## 5.1 Session Login Screen

Surface:

```text
ragcli login --email <email>
ragcli ui
```

API:

```text
POST /auth/login
```

Screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ Context Engine CLI                                           │
│ Breadcrumb: Session > Login                                  │
├──────────────────────────────────────────────────────────────┤
│ Backend: http://127.0.0.1:8000                               │
│                                                              │
│ > Email:    [admin@example.com____________________]           │
│   Password: [********_____________________________]           │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ API Call                                                     │
│  POST /auth/login                                            │
│                                                              │
│ Request                                                      │
│  email + password                                            │
│                                                              │
│ Response                                                     │
│  access_token                                                │
├──────────────────────────────────────────────────────────────┤
│ Controls                                                     │
│  Tab/Up/Down Next field   Enter Submit   Q Quit              │
└──────────────────────────────────────────────────────────────┘
```

Success screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ Login                                                        │
│ API Group: auth                                              │
├──────────────────────────────────────────────────────────────┤
│ Summary                                                      │
│  backend: http://127.0.0.1:8000                              │
│  email: admin@example.com                                    │
│  status: success                                             │
│                                                              │
│ Saved session                                                │
│ +----------------+---------------------------+               │
│ | field          | value                     |               │
│ +----------------+---------------------------+               │
│ | API base URL   | http://127.0.0.1:8000     |               │
│ | Token stored   | yes                       |               │
│ | Password saved | no                        |               │
│ +----------------+---------------------------+               │
│                                                              │
│ Next actions                                                 │
│  [1] Current session   ragcli auth me                        │
│  [2] Documents         ragcli documents list                 │
└──────────────────────────────────────────────────────────────┘
```

Error screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ Login Failed                                                 │
│ Breadcrumb: Session > Login Failed                           │
├──────────────────────────────────────────────────────────────┤
│ ERROR                                                        │
│  auth_failed: Invalid email or password                      │
│                                                              │
│ > Retry                                                      │
│   Quit                                                       │
├──────────────────────────────────────────────────────────────┤
│ Controls                                                     │
│  Up/Down Select   Enter Choose   Q Quit                      │
└──────────────────────────────────────────────────────────────┘
```

Flow:

```text
User enters email/password
        ↓
CLI sends POST /auth/login
        ↓
Backend returns access_token
        ↓
CLI stores token in local credential store/keyring fallback
        ↓
TUI resets to authenticated main menu
```

---

## 5.2 Current Session Screen

Surface:

```text
ragcli auth me
```

API:

```text
GET /auth/me
```

Screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ Current Session                                              │
│ API Group: auth                                              │
├──────────────────────────────────────────────────────────────┤
│ Summary                                                      │
│  backend: http://127.0.0.1:8000                              │
│                                                              │
│ User                                                         │
│ +---------------+-----------------------+                    │
│ | field         | value                 |                    │
│ +---------------+-----------------------+                    │
│ | Email         | admin@example.com     |                    │
│ | Role          | admin                 |                    │
│ | Authenticated | True                  |                    │
│ +---------------+-----------------------+                    │
│                                                              │
│ Actions                                                      │
│  [1] Documents         ragcli documents list                 │
│  [2] Admin documents   ragcli admin documents list           │
└──────────────────────────────────────────────────────────────┘
```

Error screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ AUTH REQUIRED                                                │
├──────────────────────────────────────────────────────────────┤
│ auth_required: Run `ragcli login` first.                     │
│                                                              │
│ Next                                                         │
│  ragcli login --email admin@example.com                      │
└──────────────────────────────────────────────────────────────┘
```

---

## 5.3 Authenticated Main Menu Screen

Surface:

```text
ragcli ui
```

Startup API when saved token exists:

```text
GET /auth/me
```

Screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ Context Engine                                               │
├──────────────────────────────────────────────────────────────┤
│ Backend: http://127.0.0.1:8000                               │
│ Session: admin@example.com                                   │
│                                                              │
│ > Documents                                                  │
│   Retrieval                                                  │
│   LightRAG Graphs                                            │
│   Admin Documents                                            │
│   Jobs                                                       │
│   Observability                                              │
│   Backend Gaps                                               │
│   Logout                                                     │
│   Quit                                                       │
├──────────────────────────────────────────────────────────────┤
│ Controls                                                     │
│  Up/Down Move   Enter Select   B Stay   Q Quit               │
└──────────────────────────────────────────────────────────────┘
```

Flow:

```text
ragcli ui starts
        ↓
Credential store has token?
        ↓ yes                                      ↓ no
GET /auth/me                                      Show Login screen
        ↓
Valid token?
        ↓ yes                                      ↓ no
Main Menu                                         Clear token, show Login screen
```

---

## 5.4 Documents Library Screen

Surfaces:

```text
ragcli documents list
ragcli screen documents
ragcli ui > Documents
```

API:

```text
GET /documents
```

Screen with documents:

```text
┌──────────────────────────────────────────────────────────────┐
│ Documents > Library                                          │
├──────────────────────────────────────────────────────────────┤
│ +--------------------------------------+----------------+--------+
│ | id                                   | filename       | status |
│ +--------------------------------------+----------------+--------+
│ | > doc_01f8a9...                      | manual.pdf     | ready  |
│ |   doc_05bc2d...                      | policy.pdf     | ready  |
│ |   doc_09ad31...                      | catalog.pdf    | ready  |
│ +--------------------------------------+----------------+--------+
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ API Call                                                     │
│  GET /documents                                              │
│                                                              │
│ Actions                                                      │
│  Enter Open selected document                                │
│  U     Upload document                                       │
├──────────────────────────────────────────────────────────────┤
│ Controls                                                     │
│  Up/Down Select document   Enter Open   U Upload             │
│  Ctrl+R Refresh   B Back   Q Quit                            │
└──────────────────────────────────────────────────────────────┘
```

Empty state:

```text
┌──────────────────────────────────────────────────────────────┐
│ Documents > Library                                          │
├──────────────────────────────────────────────────────────────┤
│ No documents found.                                          │
│                                                              │
│ > Upload document                                            │
│   Refresh                                                    │
│   Back                                                       │
│   Quit                                                       │
├──────────────────────────────────────────────────────────────┤
│ Controls                                                     │
│  Up/Down Select   Enter Choose   Ctrl+R Refresh              │
│  B Back   Q Quit                                             │
└──────────────────────────────────────────────────────────────┘
```

Error state:

```text
┌──────────────────────────────────────────────────────────────┐
│ Documents > Library                                          │
├──────────────────────────────────────────────────────────────┤
│ ERROR                                                        │
│  connection_failed: Could not connect to backend             │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ Controls                                                     │
│  Ctrl+R Refresh   B Back   Q Quit                            │
└──────────────────────────────────────────────────────────────┘
```

Flow:

```text
User opens Documents
        ↓
CLI sends GET /documents
        ↓
Backend returns ready documents only
        ↓
CLI renders ASCII table
        ↓
User selects a row and presses Enter
        ↓
CLI opens Document Detail screen
```

---

## 5.5 Document Detail Screen

Surface:

```text
ragcli documents show --document-id <document_id>
ragcli ui > Documents > selected document
```

API:

```text
GET /documents/{document_id}
```

Screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ Documents > Detail                                           │
├──────────────────────────────────────────────────────────────┤
│ +-------------+--------------------------------------+        │
│ | field       | value                                |        │
│ +-------------+--------------------------------------+        │
│ | Document ID | doc_01f8a9...                        |        │
│ | Filename    | manual.pdf                           |        │
│ | Status      | ready                                |        │
│ | Pages       | 124                                  |        │
│ | Created     | 2026-05-15T13:22:00                  |        │
│ | Updated     | 2026-05-15T13:25:00                  |        │
│ +-------------+--------------------------------------+        │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ API Call                                                     │
│  GET /documents/{document_id}                                │
│                                                              │
│ Related CLI Actions                                          │
│  ragcli documents structure --document-id <document_id>      │
│  ragcli documents page --document-id <id> --page-number 1    │
│  ragcli documents retrieve --query "..." --document-id <id>  │
├──────────────────────────────────────────────────────────────┤
│ Controls                                                     │
│  Ctrl+R Refresh   B Back   Q Quit                            │
└──────────────────────────────────────────────────────────────┘
```

Error state:

```text
┌──────────────────────────────────────────────────────────────┐
│ Documents > Detail                                           │
├──────────────────────────────────────────────────────────────┤
│ ERROR                                                        │
│  not_found: Document not found                               │
│                                                              │
│ Controls                                                     │
│  Ctrl+R Refresh   B Back   Q Quit                            │
└──────────────────────────────────────────────────────────────┘
```

---

## 5.6 Document Structure Screen

Surface:

```text
ragcli documents structure --document-id <document_id>
```

API:

```text
GET /documents/{document_id}/structure
```

Screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ Document Structure                                           │
│ API Group: documents                                         │
├──────────────────────────────────────────────────────────────┤
│ Summary                                                      │
│  document_id: doc_01f8a9...                                  │
│                                                              │
│ +-------+-------------------------------+-----------+        │
│ | level | title                         | pages     |        │
│ +-------+-------------------------------+-----------+        │
│ | 1     | Introduction                  | 1-4       |        │
│ | 1     | Installation                  | 5-18      |        │
│ | 2     | Pendant Reset                 | 19-21     |        │
│ | 1     | Troubleshooting               | 88-104    |        │
│ +-------+-------------------------------+-----------+        │
│                                                              │
│ Actions                                                      │
│  [1] Open page        ragcli documents page --document-id ...│
│  [2] Retrieve section ragcli documents retrieve --query ...  │
└──────────────────────────────────────────────────────────────┘
```

Error state:

```text
┌──────────────────────────────────────────────────────────────┐
│ Document Structure                                           │
├──────────────────────────────────────────────────────────────┤
│ ERROR                                                        │
│  not_found: Document structure not found                     │
└──────────────────────────────────────────────────────────────┘
```

---

## 5.7 Document Page Screen

Surface:

```text
ragcli documents page --document-id <document_id> --page-number <n>
```

API:

```text
GET /documents/{document_id}/pages/{page_number}
```

Screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ Document Page                                                │
│ API Group: documents                                         │
├──────────────────────────────────────────────────────────────┤
│ +-------------+--------------------------+                   │
│ | field       | value                    |                   │
│ +-------------+--------------------------+                   │
│ | Document ID | doc_01f8a9...            |                   │
│ | Filename    | manual.pdf               |                   │
│ | Page        | 19                       |                   │
│ | Section     | Pendant Reset            |                   │
│ +-------------+--------------------------+                   │
│                                                              │
│ Content                                                      │
│  This page contains the parsed text for page 19.             │
│  The CLI displays the text as a readable terminal block.      │
│                                                              │
│ Actions                                                      │
│  [1] Previous page                                           │
│  [2] Next page                                               │
│  [3] Retrieve                                                │
└──────────────────────────────────────────────────────────────┘
```

Error state:

```text
┌──────────────────────────────────────────────────────────────┐
│ Document Page                                                │
├──────────────────────────────────────────────────────────────┤
│ ERROR                                                        │
│  not_found: Page not found                                   │
└──────────────────────────────────────────────────────────────┘
```

---

## 5.8 Upload Document Screen

Surfaces:

```text
ragcli admin documents upload --file ./manual.pdf
ragcli admin documents upload-flow --file ./manual.pdf
ragcli ui > Documents > U Upload
```

API:

```text
POST /admin/documents/upload
```

Access:

```text
Admin only
```

Screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ Admin Documents > Upload                                     │
├──────────────────────────────────────────────────────────────┤
│ File path:                                                   │
│  [ ./manual.pdf________________________________________ ]     │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ API Call                                                     │
│  POST /admin/documents/upload                                │
│                                                              │
│ Request                                                      │
│  multipart/form-data field: file                             │
│                                                              │
│ Response                                                     │
│  document metadata + optional job_id                         │
├──────────────────────────────────────────────────────────────┤
│ Controls                                                     │
│  Enter Submit   Tab Next field   B Back   Q Quit             │
└──────────────────────────────────────────────────────────────┘
```

Success screen with local indexing job:

```text
┌──────────────────────────────────────────────────────────────┐
│ Admin Documents > Upload                                     │
├──────────────────────────────────────────────────────────────┤
│ SUCCESS                                                      │
│  Upload complete.                                            │
│                                                              │
│ +-------------+-----------------------------+                │
│ | field       | value                       |                │
│ +-------------+-----------------------------+                │
│ | File        | manual.pdf                  |                │
│ | Document ID | doc_01f8a9...               |                │
│ | Status      | uploaded                    |                │
│ | Job ID      | job_77b32c...               |                │
│ +-------------+-----------------------------+                │
│                                                              │
│ > View job status                                            │
│   Show full IDs                                              │
│   Return to documents                                        │
│   Upload another document                                    │
│   Quit                                                       │
├──────────────────────────────────────────────────────────────┤
│ Controls                                                     │
│  Up/Down Select   Enter Choose   B Back   Q Quit             │
└──────────────────────────────────────────────────────────────┘
```

Success screen when forwarded to remote LightRAG:

```text
┌──────────────────────────────────────────────────────────────┐
│ Admin Documents > Upload                                     │
├──────────────────────────────────────────────────────────────┤
│ SUCCESS                                                      │
│  Upload complete.                                            │
│                                                              │
│ +--------------+-----------------------------+               │
│ | field        | value                       |               │
│ +--------------+-----------------------------+               │
│ | File         | manual.pdf                  |               │
│ | Document ID  | doc_01f8a9...               |               │
│ | Status       | forwarded_to_lightrag       |               │
│ | Local job ID | none                        |               │
│ +--------------+-----------------------------+               │
│                                                              │
│ > Return to documents                                        │
│   Show full IDs                                              │
│   Upload another document                                    │
│   View LightRAG labels                                       │
│   Quit                                                       │
└──────────────────────────────────────────────────────────────┘
```

File not found error:

```text
┌──────────────────────────────────────────────────────────────┐
│ Admin Documents > Upload > Error                             │
├──────────────────────────────────────────────────────────────┤
│ ERROR                                                        │
│  file_not_found: Could not find file:                        │
│  ./missing.pdf                                               │
│                                                              │
│ > Edit file path                                             │
│   Back                                                       │
│   Quit                                                       │
├──────────────────────────────────────────────────────────────┤
│ Controls                                                     │
│  Up/Down Select   Enter Choose   B Back   Q Quit             │
└──────────────────────────────────────────────────────────────┘
```

Forbidden error:

```text
┌──────────────────────────────────────────────────────────────┐
│ Admin Documents > Upload > Forbidden                         │
├──────────────────────────────────────────────────────────────┤
│ ERROR                                                        │
│  forbidden: Admin access required                            │
│                                                              │
│ The backend rejected this upload request.                    │
├──────────────────────────────────────────────────────────────┤
│ Controls                                                     │
│  B Back   Q Quit                                             │
└──────────────────────────────────────────────────────────────┘
```

Flow:

```text
User enters file path
        ↓
CLI checks local path exists and is a file
        ↓
CLI reads file bytes
        ↓
CLI sends POST /admin/documents/upload
        ↓
Backend stores document and creates/forwards indexing work
        ↓
CLI shows upload result and optional job action
```

---

## 5.9 Admin Documents Screen

Surface:

```text
ragcli admin documents list
ragcli ui > Admin Documents
```

API:

```text
GET /admin/documents
```

Access:

```text
Admin only
```

Screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ Admin Documents                                              │
├──────────────────────────────────────────────────────────────┤
│ +----------------+-------------+---------+------------+-------------+
│ | id             | filename    | status  | indexed_by | updated_at  |
│ +----------------+-------------+---------+------------+-------------+
│ | doc_01f8a9...  | manual.pdf  | ready   | local      | 2026-05-15  |
│ | doc_05bc2d...  | policy.pdf  | failed  | lightrag   | 2026-05-15  |
│ +----------------+-------------+---------+------------+-------------+
│                                                              │
│ Actions                                                      │
│  [1] Upload    ragcli admin documents upload --file          │
│  [2] Index     ragcli admin documents index --document-id    │
│  [3] Reindex   ragcli admin documents reindex --document-id  │
│  [4] Delete    ragcli admin documents delete --document-id   │
├──────────────────────────────────────────────────────────────┤
│ Controls                                                     │
│  Ctrl+R Refresh   B Back   Q Quit                            │
└──────────────────────────────────────────────────────────────┘
```

Current TUI note:

```text
The TUI shows the admin document list, but index/reindex/delete are not yet
selectable row actions in the interactive screen. They are available as direct
Typer commands.
```

---

## 5.10 Admin Document Action Screens

Surfaces:

```text
ragcli admin documents index --document-id <document_id>
ragcli admin documents reindex --document-id <document_id>
ragcli admin documents delete --document-id <document_id>
```

APIs:

```text
POST   /admin/documents/{document_id}/index
POST   /admin/documents/{document_id}/reindex
DELETE /admin/documents/{document_id}
```

Index/reindex result screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ Admin Document index                                         │
│ API Group: admin                                             │
├──────────────────────────────────────────────────────────────┤
│ Request                                                      │
│ +-------------+------------------+                          │
│ | field       | value            |                          │
│ +-------------+------------------+                          │
│ | Document ID | doc_01f8a9...    |                          │
│ | Action      | index            |                          │
│ +-------------+------------------+                          │
│                                                              │
│ Result                                                       │
│ +--------+------------------+                                │
│ | field  | value            |                                │
│ +--------+------------------+                                │
│ | Status | accepted         |                                │
│ | Job ID | job_77b32c...    |                                │
│ +--------+------------------+                                │
│                                                              │
│ Actions                                                      │
│  [1] Check job   ragcli jobs status --job-id job_77b32c...   │
└──────────────────────────────────────────────────────────────┘
```

Delete result screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ Admin Document delete                                        │
│ API Group: admin                                             │
├──────────────────────────────────────────────────────────────┤
│ Deleted                                                      │
│ +-------------+------------------+                          │
│ | field       | value            |                          │
│ +-------------+------------------+                          │
│ | Document ID | doc_01f8a9...    |                          │
│ | Filename    | manual.pdf       |                          │
│ | Status      | deleted          |                          │
│ +-------------+------------------+                          │
│                                                              │
│ Actions                                                      │
│  [1] List documents   ragcli admin documents list            │
└──────────────────────────────────────────────────────────────┘
```

Recommended confirmation screen before delete:

```text
┌──────────────────────────────────────────────────────────────┐
│ Admin Documents > Delete Confirmation                        │
├──────────────────────────────────────────────────────────────┤
│ You are about to delete:                                     │
│                                                              │
│  Document ID: doc_01f8a9...                                  │
│  Filename:    manual.pdf                                     │
│                                                              │
│ This should soft-delete the document through the backend.     │
│                                                              │
│ > Cancel                                                     │
│   Delete document                                            │
├──────────────────────────────────────────────────────────────┤
│ API Call if confirmed                                        │
│  DELETE /admin/documents/{document_id}                       │
├──────────────────────────────────────────────────────────────┤
│ Controls                                                     │
│  Up/Down Select   Enter Choose   B Back   Q Quit             │
└──────────────────────────────────────────────────────────────┘
```

---

## 5.11 Retrieval Prompt Screen

Surfaces:

```text
ragcli documents retrieve --query "..."
ragcli screen retrieval --query "..."
ragcli ui > Retrieval
```

API:

```text
POST /query/retrieve
```

Screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ Retrieval > Context                                          │
├──────────────────────────────────────────────────────────────┤
│ Query:           [reset procedure________________________]    │
│ Mode:            auto                                        │
│ Top K:           8                                           │
│ Document filter: none                                        │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ API Call                                                     │
│  POST /query/retrieve                                        │
│                                                              │
│ Request payload                                              │
│  query, mode, top_k, include_debug, allow_general_fallback   │
├──────────────────────────────────────────────────────────────┤
│ Controls                                                     │
│  M Mode   K Top K   Enter Retrieve   B Back   Q Quit         │
└──────────────────────────────────────────────────────────────┘
```

Validation state:

```text
┌──────────────────────────────────────────────────────────────┐
│ Retrieval > Context                                          │
├──────────────────────────────────────────────────────────────┤
│ WARNING                                                      │
│  Query is required.                                          │
│                                                              │
│ Query:           []                                          │
│ Mode:            auto                                        │
│ Top K:           8                                           │
│ Document filter: none                                        │
└──────────────────────────────────────────────────────────────┘
```

Flow:

```text
User types query
        ↓
Optional: M cycles auto/semantic/navigation/hybrid
        ↓
Optional: K increases top_k
        ↓
Enter submits POST /query/retrieve
        ↓
Backend returns evidence list
        ↓
CLI opens Retrieval Result screen
```

---

## 5.12 Retrieval Result Screen

Surface:

```text
ragcli documents retrieve --query "reset procedure" --mode auto --top-k 8
```

API:

```text
POST /query/retrieve
```

Screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ Retrieval > Context                                          │
├──────────────────────────────────────────────────────────────┤
│ Request                                                      │
│ +------------------+---------+                               │
│ | field            | value   |                               │
│ +------------------+---------+                               │
│ | Requested mode   | auto    |                               │
│ | Top K            | 8       |                               │
│ | Document filter  | none    |                               │
│ | General fallback | False   |                               │
│ | Debug requested  | False   |                               │
│ +------------------+---------+                               │
│                                                              │
│ Results                                                      │
│ +---+-------------+----------+-------+-------+---------------+
│ | # | source      | engine   | score | pages | section       |
│ +---+-------------+----------+-------+-------+---------------+
│ | 1 | doc_01f...  | semantic | 0.91  | 19-21 | Pendant Reset |
│ | 2 | doc_05b...  | graph    | 0.84  | 7     | Setup         |
│ +---+-------------+----------+-------+-------+---------------+
│                                                              │
│ > Generate answer                                            │
│   Compare modes                                              │
│   Back                                                       │
│   Quit                                                       │
├──────────────────────────────────────────────────────────────┤
│ Controls                                                     │
│  Up/Down Select   Enter Choose   B Back   Q Quit             │
└──────────────────────────────────────────────────────────────┘
```

Error screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ Error                                                        │
├──────────────────────────────────────────────────────────────┤
│ ERROR                                                        │
│  connection_failed: Could not connect to backend             │
│                                                              │
│ Controls                                                     │
│  B Back   Q Quit                                             │
└──────────────────────────────────────────────────────────────┘
```

---

## 5.13 Answer Screen

Surfaces:

```text
ragcli documents answer --query "..."
ragcli query --query "..."
ragcli ui > Retrieval > Generate answer
```

APIs:

```text
POST /query/answer
POST /query
```

Screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ Retrieval > Answer                                           │
├──────────────────────────────────────────────────────────────┤
│ Answer                                                       │
│                                                              │
│  The reset procedure is summarized here using retrieved       │
│  evidence from the indexed documents.                         │
│                                                              │
│ Sources                                                      │
│ +---+-------------+-------+---------------+-------+          │
│ | # | source      | pages | section       | score |          │
│ +---+-------------+-------+---------------+-------+          │
│ | 1 | doc_01f...  | 19-21 | Pendant Reset | 0.91  |          │
│ | 2 | doc_05b...  | 7     | Setup         | 0.84  |          │
│ +---+-------------+-------+---------------+-------+          │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ Controls                                                     │
│  B Back   Q Quit                                             │
└──────────────────────────────────────────────────────────────┘
```

---

## 5.14 Retrieval Compare Screen

Surface:

```text
ragcli retrieval compare --query "..." --top-k 5
ragcli ui > Retrieval > Compare modes
```

API:

```text
POST /query/retrieve
```

Expected behavior:

```text
The compare flow calls the retrieve endpoint multiple times with different
retrieval modes, then renders a side-by-side summary.
```

Screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ Retrieval > Compare Modes                                    │
├──────────────────────────────────────────────────────────────┤
│ Query: reset procedure                                       │
│ Top K: 5                                                     │
│                                                              │
│ +------------+----------------+----------------+-------------+
│ | mode       | evidence_count | top_score      | status      |
│ +------------+----------------+----------------+-------------+
│ | semantic   | 5              | 0.91           | ok          |
│ | navigation | 3              | 0.77           | ok          |
│ | hybrid     | 5              | 0.94           | ok          |
│ +------------+----------------+----------------+-------------+
│                                                              │
│ Developer note                                               │
│  Use this screen to sanity-check which retrieval path works   │
│  best for a question before wiring the future frontend.       │
├──────────────────────────────────────────────────────────────┤
│ Controls                                                     │
│  B Back   Q Quit                                             │
└──────────────────────────────────────────────────────────────┘
```

---

## 5.15 Jobs Screen

Surfaces:

```text
ragcli jobs list
ragcli ui > Jobs
```

API:

```text
GET /jobs
```

Access:

```text
Admin only
```

Screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ Jobs                                                         │
├──────────────────────────────────────────────────────────────┤
│ +-------------+----------------+---------+-------------+-------------+
│ | id          | kind           | status  | document_id | updated_at  |
│ +-------------+----------------+---------+-------------+-------------+
│ | job_77b...  | index_document | running | doc_01f...  | 2026-05-15  |
│ | job_88c...  | index_document | failed  | doc_05b...  | 2026-05-15  |
│ +-------------+----------------+---------+-------------+-------------+
│                                                              │
│ Actions                                                      │
│  [1] Job status   ragcli jobs status --job-id job_77b...     │
├──────────────────────────────────────────────────────────────┤
│ Controls                                                     │
│  Ctrl+R Refresh   B Back   Q Quit                            │
└──────────────────────────────────────────────────────────────┘
```

Forbidden error:

```text
┌──────────────────────────────────────────────────────────────┐
│ Jobs                                                         │
├──────────────────────────────────────────────────────────────┤
│ ERROR                                                        │
│  forbidden: Admin access required                            │
│                                                              │
│ Controls                                                     │
│  Ctrl+R Refresh   B Back   Q Quit                            │
└──────────────────────────────────────────────────────────────┘
```

---

## 5.16 Job Status Screen

Surface:

```text
ragcli jobs status --job-id <job_id>
```

API:

```text
GET /jobs/{job_id}
```

Screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ Job Status                                                   │
│ API Group: jobs                                              │
├──────────────────────────────────────────────────────────────┤
│ +-------------+----------------------------+                 │
│ | field       | value                      |                 │
│ +-------------+----------------------------+                 │
│ | Job ID      | job_77b32c...              |                 │
│ | Type        | index_document             |                 │
│ | Status      | running                    |                 │
│ | Document ID | doc_01f8a9...              |                 │
│ | Created     | 2026-05-15T13:22:00        |                 │
│ | Updated     | 2026-05-15T13:25:00        |                 │
│ +-------------+----------------------------+                 │
│                                                              │
│ Actions                                                      │
│  [1] Show document   ragcli documents show --document-id ... │
└──────────────────────────────────────────────────────────────┘
```

Failed job screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ Job Status                                                   │
├──────────────────────────────────────────────────────────────┤
│ +-------------+----------------------------+                 │
│ | field       | value                      |                 │
│ +-------------+----------------------------+                 │
│ | Job ID      | job_88c44d...              |                 │
│ | Type        | index_document             |                 │
│ | Status      | failed                     |                 │
│ | Document ID | doc_05bc2d...              |                 │
│ +-------------+----------------------------+                 │
│                                                              │
│ Error                                                        │
│  Parser failed for uploaded file.                            │
│                                                              │
│ Actions                                                      │
│  [1] Retry job       ragcli jobs retry --job-id job_88c44d...│
│  [2] Delete document ragcli admin documents delete --document-id ...
└──────────────────────────────────────────────────────────────┘
```

---

## 5.17 Job Retry Screen

Surface:

```text
ragcli jobs retry --job-id <job_id>
```

API:

```text
POST /jobs/{job_id}/retry
```

Screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ Job Retry                                                    │
│ API Group: jobs                                              │
├──────────────────────────────────────────────────────────────┤
│ Request                                                      │
│ +--------------+------------------+                         │
│ | field        | value            |                         │
│ +--------------+------------------+                         │
│ | Previous Job | job_88c44d...    |                         │
│ | Action       | retry            |                         │
│ +--------------+------------------+                         │
│                                                              │
│ Result                                                       │
│ +------------+------------------+                           │
│ | field      | value            |                           │
│ +------------+------------------+                           │
│ | Status     | accepted         |                           │
│ | New Job ID | job_99d55e...    |                           │
│ +------------+------------------+                           │
│                                                              │
│ Actions                                                      │
│  [1] Job status   ragcli jobs status --job-id job_99d55e...  │
└──────────────────────────────────────────────────────────────┘
```

---

## 5.18 LightRAG Labels Screen

Surfaces:

```text
ragcli lightrag labels list
ragcli lightrag labels popular --limit 20
ragcli lightrag labels search --query "bearing" --limit 20
ragcli ui > LightRAG Graphs
```

APIs:

```text
GET /graph/label/list
GET /graph/label/popular?limit=<limit>
GET /graph/label/search?q=<query>&limit=<limit>
```

Screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ LightRAG > Labels                                            │
├──────────────────────────────────────────────────────────────┤
│ +----+----------------------+-------+                        │
│ | #  | label                | count |                        │
│ +----+----------------------+-------+                        │
│ | 1  | pendant reset        | 18    |                        │
│ | 2  | hospital bed         | 14    |                        │
│ | 3  | control box          | 9     |                        │
│ +----+----------------------+-------+                        │
│                                                              │
│ Actions                                                      │
│  [1] Show graph   ragcli lightrag graphs show --label        │
├──────────────────────────────────────────────────────────────┤
│ Controls                                                     │
│  Ctrl+R Refresh   B Back   Q Quit                            │
└──────────────────────────────────────────────────────────────┘
```

Disabled LightRAG error:

```text
┌──────────────────────────────────────────────────────────────┐
│ LightRAG > Labels                                            │
├──────────────────────────────────────────────────────────────┤
│ ERROR                                                        │
│  bad_request: LightRAG is disabled                           │
│                                                              │
│ Next                                                         │
│  Check app settings and LightRAG remote adapter config.       │
└──────────────────────────────────────────────────────────────┘
```

---

## 5.19 LightRAG Graph Screen

Surfaces:

```text
ragcli lightrag graphs show --label "pendant reset" --max-depth 3 --max-nodes 1000
ragcli screen graph --label "pendant reset"
```

API:

```text
GET /graphs?label=<label>&max_depth=<n>&max_nodes=<n>
```

Screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ LightRAG Graph                                               │
│ API Group: lightrag                                          │
├──────────────────────────────────────────────────────────────┤
│ Summary                                                      │
│  label: pendant reset                                        │
│                                                              │
│ Request                                                      │
│ +-----------+-------+                                        │
│ | field     | value |                                        │
│ +-----------+-------+                                        │
│ | Max depth | 3     |                                        │
│ | Max nodes | 1000  |                                        │
│ +-----------+-------+                                        │
│                                                              │
│ Graph Summary                                                │
│ +----------------+-------+                                   │
│ | field          | value |                                   │
│ +----------------+-------+                                   │
│ | Nodes          | 84    |                                   │
│ | Edges          | 131   |                                   │
│ | Depth returned | 3     |                                   │
│ +----------------+-------+                                   │
│                                                              │
│ Top connected labels                                         │
│ +----+-------------------+--------------+                   │
│ | #  | label             | relationship |                   │
│ +----+-------------------+--------------+                   │
│ | 1  | control box       | 12           |                   │
│ | 2  | remote pendant    | 9            |                   │
│ | 3  | reset sequence    | 7            |                   │
│ +----+-------------------+--------------+                   │
│                                                              │
│ Actions                                                      │
│  [1] Export graph JSON                                       │
└──────────────────────────────────────────────────────────────┘
```

---

## 5.20 Observability Screen

Surfaces:

```text
ragcli admin query-logs list
ragcli admin audit-logs list
ragcli ui > Observability
```

APIs:

```text
GET /admin/query-logs
GET /admin/audit-logs
```

Access:

```text
Admin only
```

Screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ Observability                                                │
├──────────────────────────────────────────────────────────────┤
│ Query Logs                                                   │
│ +---------------------+----------+--------+-------+----------+
│ | created_at          | user     | mode   | top_k | query    |
│ +---------------------+----------+--------+-------+----------+
│ | 2026-05-15 13:22    | admin    | auto   | 8     | reset... |
│ | 2026-05-15 13:35    | user     | hybrid | 5     | setup... |
│ +---------------------+----------+--------+-------+----------+
│                                                              │
│ Audit Logs                                                   │
│ +---------------------+----------+----------------+---------+
│ | created_at          | user     | event          | status  |
│ +---------------------+----------+----------------+---------+
│ | 2026-05-15 13:20    | admin    | document_upload| success |
│ | 2026-05-15 13:25    | admin    | document_index | success |
│ +---------------------+----------+----------------+---------+
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ Controls                                                     │
│  Ctrl+R Refresh   B Back   Q Quit                            │
└──────────────────────────────────────────────────────────────┘
```

Non-admin error state:

```text
┌──────────────────────────────────────────────────────────────┐
│ Observability                                                │
├──────────────────────────────────────────────────────────────┤
│ ERROR                                                        │
│  forbidden: Admin access required                            │
│                                                              │
│ Query logs and audit logs are admin-only.                    │
├──────────────────────────────────────────────────────────────┤
│ Controls                                                     │
│  Ctrl+R Refresh   B Back   Q Quit                            │
└──────────────────────────────────────────────────────────────┘
```

---

## 5.21 Admin Dashboard Screen

Surface:

```text
ragcli admin dashboard
ragcli screen admin
```

APIs:

```text
GET /admin/documents
GET /jobs
GET /admin/query-logs
GET /admin/audit-logs
```

Access:

```text
Admin only
```

Screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ Admin Dashboard                                              │
├──────────────────────────────────────────────────────────────┤
│ Documents                                                    │
│ +------------+-------+                                       │
│ | status     | count |                                       │
│ +------------+-------+                                       │
│ | ready      | 18    |                                       │
│ | uploaded   | 2     |                                       │
│ | failed     | 1     |                                       │
│ +------------+-------+                                       │
│                                                              │
│ Jobs                                                         │
│ +------------+-------+                                       │
│ | status     | count |                                       │
│ +------------+-------+                                       │
│ | queued     | 1     |                                       │
│ | running    | 1     |                                       │
│ | failed     | 1     |                                       │
│ +------------+-------+                                       │
│                                                              │
│ Recent activity                                              │
│  - latest query logs                                         │
│  - latest audit logs                                         │
└──────────────────────────────────────────────────────────────┘
```

Note:

```text
This is a useful operator overview, but it should stay lightweight. Avoid turning
this into a full monitoring system unless the app needs it.
```

---

## 5.22 Backend Gaps Screen

Surfaces:

```text
ragcli screen gaps
ragcli ui > Backend Gaps
```

API:

```text
None. This screen is local documentation generated from cli/screens/planned.py.
```

Screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ Backend Gaps                                                 │
├──────────────────────────────────────────────────────────────┤
│ Planned Unsupported Surfaces                                 │
│ +--------------------------------------+----------------------+
│ | command                              | status               |
│ +--------------------------------------+----------------------+
│ | ragcli chat                          | not_supported_by_backend |
│ | ragcli users list                    | not_supported_by_backend |
│ | ragcli conversations list            | not_supported_by_backend |
│ | ragcli messages list                 | not_supported_by_backend |
│ | ragcli runs status                   | not_supported_by_backend |
│ | ragcli runs approvals list           | not_supported_by_backend |
│ | ragcli admin corpus publish          | not_supported_by_backend |
│ | ragcli admin corpus rollback         | not_supported_by_backend |
│ | ragcli admin corpus cleanup          | not_supported_by_backend |
│ +--------------------------------------+----------------------+
├──────────────────────────────────────────────────────────────┤
│ Controls                                                     │
│  Ctrl+R Refresh   B Back   Q Quit                            │
└──────────────────────────────────────────────────────────────┘
```

Single unsupported command screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ Backend Gap                                                  │
├──────────────────────────────────────────────────────────────┤
│ not_supported_by_backend                                     │
│  `ragcli users list` needs a backend route first.             │
│                                                              │
│ Reason                                                       │
│ +---------------+-------------------------+                  │
│ | field         | value                   |                  │
│ +---------------+-------------------------+                  │
│ | Capability    | user listing            |                  │
│ | Current route | none                    |                  │
│ | Suggested API | GET /users              |                  │
│ +---------------+-------------------------+                  │
│                                                              │
│ Action                                                       │
│  Implement backend route: docs/cli_docs/api-contract.md       │
└──────────────────────────────────────────────────────────────┘
```

---

## 5.23 Logout Screen

Surfaces:

```text
ragcli logout
ragcli ui > Logout
```

API:

```text
None. Local credential store clear only.
```

Screen:

```text
┌──────────────────────────────────────────────────────────────┐
│ Session > Logged Out                                         │
├──────────────────────────────────────────────────────────────┤
│ SUCCESS                                                      │
│  Your local CLI session has been cleared.                    │
│                                                              │
│ > Login again                                                │
│   Quit                                                       │
├──────────────────────────────────────────────────────────────┤
│ Controls                                                     │
│  Up/Down Select   Enter Choose   Q Quit                      │
└──────────────────────────────────────────────────────────────┘
```

---

# 6. Planned / Unsupported CLI Surfaces

The CLI currently includes planned commands that intentionally call `_unsupported(...)` and return `not_supported_by_backend`.

```text
+----+-------------------------------------------+-------------------------------+-----------------------------+
| #  | Planned CLI Command                       | Intended Capability           | Suggested Backend Route     |
+----+-------------------------------------------+-------------------------------+-----------------------------+
| 01 | ragcli users create                       | user creation                 | POST /users                 |
| 02 | ragcli users list                         | user listing                  | GET /users                  |
| 03 | ragcli retrievers list                    | retriever registry            | GET /retrievers             |
| 04 | ragcli agents list                        | agent registry                | GET /agents                 |
| 05 | ragcli conversations create               | conversation creation         | POST /conversations         |
| 06 | ragcli conversations list                 | conversation history          | GET /conversations          |
| 07 | ragcli conversations show                 | conversation detail           | GET /conversations/{id}     |
| 08 | ragcli chat                               | interactive chat              | POST /chat or /messages     |
| 09 | ragcli messages send                      | send conversation message     | POST /messages              |
| 10 | ragcli messages list                      | list conversation messages    | GET /messages               |
| 11 | ragcli runs status                        | agent run status              | GET /runs/{run_id}          |
| 12 | ragcli runs cancel                        | cancel agent run              | POST /runs/{run_id}/cancel  |
| 13 | ragcli runs approvals list                | human approval queue          | GET /runs/approvals         |
| 14 | ragcli runs approvals approve             | approve run action            | POST /runs/approvals/{id}/approve |
| 15 | ragcli runs approvals reject              | reject run action             | POST /runs/approvals/{id}/reject  |
| 16 | ragcli admin corpus publish               | corpus version publish        | POST /admin/corpus/publish  |
| 17 | ragcli admin corpus rollback              | corpus version rollback       | POST /admin/corpus/rollback |
| 18 | ragcli admin corpus cleanup               | corpus cleanup                | POST /admin/corpus/cleanup  |
| 19 | ragcli documents content                  | page range content            | GET /documents/{id}/content |
| 20 | ragcli documents search                   | document text search          | GET /documents/search?q=    |
+----+-------------------------------------------+-------------------------------+-----------------------------+
```

Recommended rule:

```text
Do not add full TUI screens for these until the backend route exists.
Keep the current gap screen because it gives junior devs a clear boundary:
"CLI placeholder exists, but backend capability does not."
```

---

# 7. High-Value Gaps to Fix First

```text
+----+----------------------------+-----------------------------+------------------------------+
| #  | Gap                        | Why it matters              | Lightweight fix              |
+----+----------------------------+-----------------------------+------------------------------+
| 01 | No CLI health command      | Fast backend sanity check    | Add ragcli health            |
| 02 | No admin ping command      | Tests admin auth quickly     | Add ragcli admin ping        |
| 03 | TUI admin doc actions partial| CLI has commands, TUI not easy| Add row action menu        |
| 04 | TUI LightRAG graph prompt  | Can list labels but not easily| Add label input/detail screen|
| 05 | Delete lacks confirmation  | Risky admin operation        | Add confirmation screen      |
| 06 | Structure/page not in TUI   | Useful frontend-like flows   | Add detail sub-menu          |
+----+----------------------------+-----------------------------+------------------------------+
```

---

# 8. Recommended Minimal TUI Additions

## 8.1 Health Screen

Suggested command:

```bash
ragcli health
ragcli health readiness
```

Suggested APIs:

```text
GET /health
GET /health/readiness
```

ASCII:

```text
┌──────────────────────────────────────────────────────────────┐
│ Health                                                       │
├──────────────────────────────────────────────────────────────┤
│ +-----------+-------+                                        │
│ | check     | value |                                        │
│ +-----------+-------+                                        │
│ | health    | ok    |                                        │
│ | readiness | ready |                                        │
│ +-----------+-------+                                        │
│                                                              │
│ Backend: http://127.0.0.1:8000                               │
├──────────────────────────────────────────────────────────────┤
│ Controls                                                     │
│  Ctrl+R Refresh   B Back   Q Quit                            │
└──────────────────────────────────────────────────────────────┘
```

## 8.2 Admin Ping Screen

Suggested command:

```bash
ragcli admin ping
```

Suggested API:

```text
GET /admin/ping
```

ASCII:

```text
┌──────────────────────────────────────────────────────────────┐
│ Admin Ping                                                   │
├──────────────────────────────────────────────────────────────┤
│ +--------+---------------------+                             │
│ | field  | value               |                             │
│ +--------+---------------------+                             │
│ | status | ok                  |                             │
│ | admin  | admin@example.com   |                             │
│ +--------+---------------------+                             │
└──────────────────────────────────────────────────────────────┘
```

## 8.3 Admin Document Row Action Menu

Suggested placement:

```text
ragcli ui > Admin Documents > selected document
```

ASCII:

```text
┌──────────────────────────────────────────────────────────────┐
│ Admin Documents > Document Actions                           │
├──────────────────────────────────────────────────────────────┤
│ Document                                                     │
│  ID:       doc_01f8a9...                                     │
│  Filename: manual.pdf                                        │
│  Status:   ready                                             │
│                                                              │
│ > View document                                              │
│   View structure                                             │
│   View page 1                                                │
│   Index                                                      │
│   Reindex                                                    │
│   Delete                                                     │
│   Back                                                       │
├──────────────────────────────────────────────────────────────┤
│ API Calls                                                    │
│  GET    /documents/{document_id}                             │
│  GET    /documents/{document_id}/structure                   │
│  GET    /documents/{document_id}/pages/1                     │
│  POST   /admin/documents/{document_id}/index                 │
│  POST   /admin/documents/{document_id}/reindex               │
│  DELETE /admin/documents/{document_id}                       │
├──────────────────────────────────────────────────────────────┤
│ Controls                                                     │
│  Up/Down Select   Enter Choose   B Back   Q Quit             │
└──────────────────────────────────────────────────────────────┘
```

---

# 9. Implementation Notes for Junior Devs

## 9.1 Keep the CLI thin

The CLI should not duplicate backend logic. It should:

```text
collect inputs → call API route → render response → show next useful action
```

Avoid moving business logic into the CLI.

## 9.2 Keep one screen per API surface

Good pattern:

```text
API route: GET /documents
CLI:       ragcli documents list
TUI:       DocumentsScreen
Renderer:  build_document_library_screen(...)
```

This makes it easy to maintain parity between backend, CLI, and future frontend.

## 9.3 Keep admin-only surfaces obvious

Use explicit labels:

```text
Admin Documents
Admin Ping
Admin Query Logs
Admin Audit Logs
```

Do not hide admin-only behavior behind generic labels like `Settings` or `Tools`.

## 9.4 Treat planned stubs as documentation, not bugs

The unsupported commands are useful as future API contracts. Keep them, but avoid wiring them into workflows until the backend route exists.

## 9.5 Use the CLI as a future frontend map

Each screen already mirrors a future frontend capability:

```text
Documents screen      → Document library page
Retrieval screen      → Ask/retrieve page
LightRAG screen       → Graph exploration page
Admin Documents       → Admin document management page
Jobs                  → Indexing job monitor page
Observability         → Lightweight admin logs page
Backend Gaps          → Developer planning page
```

---

# 10. Final Recommendation

The CLI is already doing the right architectural job: it gives a lightweight, terminal-first way to exercise the same backend API routes that a future frontend will use.

The highest-value next improvement is not a large framework rewrite. It is a small usability pass:

```text
1. Add ragcli health and ragcli admin ping.
2. Add selectable row actions in the TUI for admin documents.
3. Add delete confirmation.
4. Add structure/page navigation from document detail.
5. Add a LightRAG graph prompt/search screen.
6. Keep planned unsupported screens as clear backend gap documentation.
```

That keeps the implementation lean, clear for junior developers, and aligned with the backend route structure.
