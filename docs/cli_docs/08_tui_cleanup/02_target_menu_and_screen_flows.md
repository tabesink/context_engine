# 2. Target Menu and Screen Flows

## 2.1 Target Root Menu

```text
CONTEXT ENGINE

Backend: http://127.0.0.1:8010
Session: admin@example.com

> Documents
  Retrieval
  Graphs
  LightRAG Domains
  Jobs
  Observability
  Health / Readiness
  Backend Gaps
  Logout
  Quit
```

For normal users:

```text
CONTEXT ENGINE

Backend: http://127.0.0.1:8010
Session: user@example.com

> Documents
  Retrieval
  Graphs
  Health / Readiness
  Logout
  Quit
```

Optional: keep `Backend Gaps` visible only in development mode.

## 2.2 Documents Screen

```text
DOCUMENTS

> Browse Ready Documents
  Search / Filter Documents
  View Document Detail
  View Structure / Outline
  View Page
  Admin Actions
  Back
```

If user is not admin:

```text
DOCUMENTS

> Browse Ready Documents
  Search / Filter Documents
  View Document Detail
  View Structure / Outline
  View Page
  Back
```

If search endpoint is still a backend gap, show:

```text
Search / Filter Documents  [backend gap]
```

or hide it until implemented.

## 2.3 Documents Admin Actions Screen

```text
DOCUMENTS > ADMIN ACTIONS

> Upload Document
  List All Documents
  Index / Reindex Document
  Delete Document
  Back
```

No top-level `Admin Documents`.

## 2.4 Retrieval Screen

```text
RETRIEVAL

> Retrieval Preview
  Citation Answer
  Compare Modes
  Domain Selector
  Back
```

Domain selector calls:

```text
GET /lightrag/domains
```

and query payloads include:

```json
{
  "lightrag_domain_id": "fatigue"
}
```

when selected.

## 2.5 Graphs Screen

```text
GRAPHS

> Graph Summary
  Label Catalog
  Popular Labels
  Search Labels
  Back
```

API calls stay the same initially:

```text
GET /graphs
GET /graph/label/list
GET /graph/label/popular
GET /graph/label/search
```

The label is changed only in the UI.

## 2.6 LightRAG Domains Screen

```text
LIGHTRAG DOMAINS

> List Domains
  Create Domain
  Show Domain Detail
  Start Domain
  Stop Domain
  Recreate Domain
  Regenerate Domain Files
  Archive Remove Domain
  Permanent Delete Domain
  Back
```

All items are admin-only. The root menu may hide `LightRAG Domains` for non-admin users, or show it and let backend return `403`. Preferred for usability: hide for non-admin users.

## 2.7 Jobs Screen

```text
JOBS

> List Jobs
  Show Job Detail
  Retry Failed Job
  Back
```

## 2.8 Observability Screen

```text
OBSERVABILITY

> Audit Logs
  Query Logs
  Back
```

If later merged into `/admin/logs?type=...`, keep the screen unchanged and only update the service helper.

## 2.9 Health / Readiness Screen

```text
HEALTH / READINESS

> API Health
  Readiness
  Storage Status
  Worker / Redis Status
  LightRAG Runtime Status
  LightRAG Deploy Status
  Back
```

Only show checks that are backed by real routes. Do not fake system status.

## 2.10 Backend Gaps Screen

```text
BACKEND GAPS

The following screens are planned but do not have backend support yet:

- Conversations
- Chat history
- Users
- Agents
- Corpus publish / rollback
- Runs / approvals

Back
```

This prevents fake success and makes gaps explicit.
