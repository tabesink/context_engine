# 5. Screen-Specific Refinements

## 5.1 Documents

### Default table

```text
+------------+----------------------+----------+-------+------------+
| id         | filename             | status   | pages | updated    |
+------------+----------------------+----------+-------+------------+
| doc_01f... | manual.pdf           | ready    | 124   | 2026-05-18 |
| doc_05b... | catalog.pdf          | ready    | 42    | 2026-05-18 |
+------------+----------------------+----------+-------+------------+
```

### Default actions

```text
> Open selected
  View structure
  View page
  Retrieve from selected
  Admin Actions        admin only
  Refresh
  Inspect API
  Back
```

### Backend routes

```text
GET /documents
GET /documents/{document_id}
GET /documents/{document_id}/structure
GET /documents/{document_id}/pages/{page_number}
```

### Inspect fields

- method and route
- status code
- latency
- document count
- selected document full ID
- raw JSON response

## 5.2 Documents > Admin Actions

### Actions

```text
> Upload document
  List all documents
  Rebuild structure
  Reingest LightRAG
  Refresh LightRAG status
  Delete selected
  Back
```

### Backend routes

```text
GET    /admin/documents
POST   /admin/documents/upload
POST   /admin/documents/{document_id}/reingest
POST   /admin/documents/{document_id}/refresh-status
DELETE /admin/documents/{document_id}
```

### Delete confirmation

```text
DELETE DOCUMENT

Document: manual.pdf
ID:       doc_01f8a9...

This should soft-delete the document through the backend.

Type DELETE doc_01f8a9 to continue:
```

## 5.3 Retrieval

### Prompt screen fields

```text
Query:              [reset procedure________________]
Mode:               auto
LightRAG domain:    fatigue
Top K:              8
Document filter:    none
General fallback:   false
Debug requested:    false
```

### Result table

```text
+---+------------+----------+-------+-------+----------------+
| # | engine     | score    | pages | doc   | section        |
+---+------------+----------+-------+-------+----------------+
| 1 | semantic   | 0.91     | 19-21 | doc_1 | Pendant Reset  |
| 2 | navigation | 0.84     | 7     | doc_5 | Setup          |
+---+------------+----------+-------+-------+----------------+
```

### Backend routes

```text
POST /retrieve
```

### Inspect fields

- full request payload
- selected `lightrag_domain_id`
- selected `document_ids`
- evidence count
- evidence IDs
- engines returned
- raw JSON

## 5.4 Graphs

Rename screen from:

```text
LightRAG Graphs
```

to:

```text
Graphs
```

### Actions

```text
> Popular labels
  Search labels
  Label catalog
  Graph summary
  Back
```

### Routes

```text
GET /graphs
GET /graph/label/list
GET /graph/label/popular
GET /graph/label/search
```

### Inspect fields

- label
- max depth
- max nodes
- node count
- edge count
- route
- raw graph JSON option

## 5.5 LightRAG Domains

### Default table

```text
+----------+------+----------+----------+---------+------------+
| domain   | port | runtime  | health   | default | updated    |
+----------+------+----------+----------+---------+------------+
| fatigue  | 9622 | running  | healthy  | yes     | 2026-05-18 |
| abaqus   | 9623 | stopped  | unknown  | no      | 2026-05-18 |
+----------+------+----------+----------+---------+------------+
```

### Actions

```text
> Create domain
  Show detail
  Start
  Stop
  Recreate
  Regenerate files
  Archive remove
  Permanent delete
  Inspect API
  Refresh
  Back
```

### Admin routes

```text
GET    /admin/lightrag/domains
POST   /admin/lightrag/domains
GET    /admin/lightrag/domains/{domain_id}
POST   /admin/lightrag/domains/{domain_id}/up
POST   /admin/lightrag/domains/{domain_id}/down
POST   /admin/lightrag/domains/{domain_id}/recreate
POST   /admin/lightrag/domains/{domain_id}/regenerate
DELETE /admin/lightrag/domains/{domain_id}
```

### User-safe route

```text
GET /lightrag/domains
```

### Inspect fields

- admin route
- domain ID
- manifest path
- storage path
- generated compose path
- last operation
- health response
- Docker operation status

Do not expose secrets.

## 5.6 Jobs

### Default table

```text
+------------+----------------+----------+------------+------------+
| job_id     | kind           | status   | document   | updated    |
+------------+----------------+----------+------------+------------+
| job_77b... | document_ingest | running  | doc_01f... | 13:25      |
| job_88c... | document_ingest | failed   | doc_05b... | 13:35      |
+------------+----------------+----------+------------+------------+
```

### Routes

```text
GET /jobs
GET /jobs/{job_id}
POST /jobs/{job_id}/retry
```

### Inspect fields

- full job ID
- full document ID
- error message
- metadata
- route
- retry response payload

## 5.7 Observability

### Default view

Keep two compact panels:

```text
Recent Query Logs
Recent Audit Logs
```

Do not show every metadata field by default.

### Routes

```text
GET /admin/query-logs
GET /admin/audit-logs
```

### Inspect fields

- log ID
- user ID
- route/action
- query/mode
- metadata
- timestamps

## 5.8 Health / Readiness

### Default table

```text
+-------------------------+----------+-----------------------------+
| check                   | status   | detail                      |
+-------------------------+----------+-----------------------------+
| API health              | ok       | /health                     |
| API readiness           | ready    | /health/readiness           |
| database                | ok       | reachable                   |
| storage                 | ok       | .data writable              |
| redis / worker          | warn     | worker heartbeat missing    |
| LightRAG runtime        | ok       | fatigue healthy             |
| LightRAG deploy control | ok       | docker reachable            |
+-------------------------+----------+-----------------------------+
```

Only show rows backed by real routes or real backend payloads.

## 5.9 Backend Gaps

### Default table

```text
+----------------------+-----------------------------+----------+-----------+
| capability           | missing route               | priority | note      |
+----------------------+-----------------------------+----------+-----------+
| document search      | GET /documents/search?q=    | medium   | planned   |
| conversations        | GET /conversations          | low      | future    |
| users admin          | GET /users                  | medium   | planned   |
+----------------------+-----------------------------+----------+-----------+
```

Rule:

```text
Backend gaps must never render as fake success.
```
