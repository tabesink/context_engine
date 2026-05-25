# 4. Progressive Disclosure Model

## 4.1 Why Progressive Disclosure

The TUI has two jobs:

1. normal operation, and
2. backend/API debugging.

If every route, payload, raw response, ID, and debug object is always visible, the screen becomes unusable. Instead, expose detail on demand.

## 4.2 Modes

| Mode | Key | Purpose |
|---|---:|---|
| Normal | default | Clean operator summary. |
| Inspect API | `I` | Method, route, params, payload, status, latency, response summary. |
| Raw JSON | `J` | Pretty-printed backend response. |
| Full IDs | `F` | Expand truncated IDs in tables/details. |
| Debug | `D` | Admin-only backend debug payload if returned. |
| Error Detail | automatic or `I` | Structured backend error and next action. |

## 4.3 API Inspect Drawer

Example:

```text
┌─ API INSPECT ────────────────────────────────────────────────┐
│ Method: POST                                                 │
│ Route:  /retrieve                                            │
│ Status: 200 OK                                               │
│ Time:   63 ms                                                │
│                                                              │
│ Request JSON                                                 │
│ {                                                            │
│   "query": "reset procedure",                                │
│   "mode": "hybrid",                                          │
│   "top_k": 8,                                                │
│   "lightrag_domain_id": "fatigue"                            │
│ }                                                            │
│                                                              │
│ Response Summary                                             │
│ evidence_count: 8                                            │
│ engines: semantic, navigation                                │
│ debug: omitted                                               │
└──────────────────────────────────────────────────────────────┘
```

## 4.4 GET Inspect Variant

```text
┌─ API INSPECT ────────────────────────────────────────────────┐
│ Method: GET                                                  │
│ Route:  /documents                                           │
│ Status: 200 OK                                               │
│ Time:   37 ms                                                │
│ Query Params: none                                           │
│                                                              │
│ Response Summary                                             │
│ documents_count: 12                                          │
│ ready_count: 12                                              │
└──────────────────────────────────────────────────────────────┘
```

## 4.5 Multipart Upload Inspect Variant

```text
┌─ API INSPECT ────────────────────────────────────────────────┐
│ Method: POST                                                 │
│ Route:  /admin/documents/upload                              │
│ Status: 202 Accepted                                         │
│ Time:   181 ms                                               │
│                                                              │
│ Multipart Request                                            │
│ file.name: manual.pdf                                        │
│ file.size: 2.4 MB                                            │
│ lightrag_domain_id: fatigue                                  │
│                                                              │
│ Response Summary                                             │
│ document_id: doc_01f8a9...                                   │
│ status: indexing                                             │
│ job_id: job_77b32c...                                        │
└──────────────────────────────────────────────────────────────┘
```

## 4.6 DELETE Inspect Variant

```text
┌─ API INSPECT ────────────────────────────────────────────────┐
│ Method: DELETE                                               │
│ Route:  /admin/lightrag/domains/fatigue                      │
│ Status: 200 OK                                               │
│ Time:   94 ms                                                │
│                                                              │
│ Request                                                      │
│ permanent: false                                             │
│ confirmation: ARCHIVE fatigue                                │
│                                                              │
│ Response Summary                                             │
│ archived: true                                               │
│ archive_path: .data/lightrag/deleted/fatigue-2026...         │
└──────────────────────────────────────────────────────────────┘
```

## 4.7 Raw JSON View

```text
┌─ RAW JSON ───────────────────────────────────────────────────┐
│ {                                                            │
│   "documents": [                                             │
│     {                                                        │
│       "id": "doc_01f8a9...",                                 │
│       "filename": "manual.pdf",                              │
│       "status": "ready"                                      │
│     }                                                        │
│   ]                                                          │
│ }                                                            │
├──────────────────────────────────────────────────────────────┤
│ Keys: J Close  F Full IDs  B Back                            │
└──────────────────────────────────────────────────────────────┘
```

Raw JSON rules:

- Pretty-print with indentation.
- Redact tokens, passwords, API keys.
- Truncate very large fields by default.
- Show filename/size for file uploads, never file bytes.
- Allow “show more” for long text fields if current TUI supports it.

## 4.8 Full ID Toggle

Default:

```text
doc_01f8a9...
job_77b32c...
```

Full ID mode:

```text
doc_01f8a9b9-8f3c-4b0a-8f9a-4c21e6a65c25
job_77b32c81-1c44-48d0-9c3c-f097df331983
```

Use `F` consistently.

## 4.9 Debug Mode

Debug mode is admin-only and only shows what the backend returned.

If backend omits debug payload:

```text
Debug: not returned by backend
```

If user is not admin:

```text
Debug: admin-only
```

Do not synthesize backend debug fields in the TUI.
