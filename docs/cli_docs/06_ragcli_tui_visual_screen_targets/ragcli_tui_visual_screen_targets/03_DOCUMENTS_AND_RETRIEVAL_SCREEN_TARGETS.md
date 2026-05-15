# Documents and Retrieval Screen Targets

These are the target ASCII views for document browsing and retrieval.

## 1. Main Menu

```text
CONTEXT ENGINE

Backend: http://127.0.0.1:8010
Session: admin@example.com

> Documents
  Retrieval
  LightRAG Graphs
  Admin Documents
  Jobs
  Observability
  Backend Gaps
  Logout
  Quit

Up/Down Select | Enter Choose | Q Quit
```

## 2. Documents Empty State

```text
DOCUMENTS

No documents found.

Recommended next step:
> Upload document
  Refresh
  Back
  Quit

Up/Down Select | Enter Choose | Ctrl+R Refresh | B Back | Q Quit
```

Do not show command hints like:

```text
Next:
  ragcli admin documents upload --file ./manual.pdf
```

Inside the TUI, the user should receive actions, not instructions to leave the TUI.

## 3. Documents With Existing Documents

```text
DOCUMENTS

+---------+--------------------------+----------+-------+------------+
| ID      | Filename                 | Status   | Pages | Updated    |
+---------+--------------------------+----------+-------+------------+
| > doc_1 | bed_manual.pdf           | ready    | 42    | 2026-05-14 |
|   doc_2 | mattress_specs.pdf       | indexing | --    | 2026-05-14 |
|   doc_3 | service_guide.pdf        | failed   | --    | 2026-05-13 |
+---------+--------------------------+----------+-------+------------+

Selected:
  bed_manual.pdf

Actions:
  Enter Open selected document
  R     Retrieve from selected document
  U     Upload document
  Ctrl+R Refresh
  B     Back
  Q     Quit
```

Notes:

- Show `Enter Open` only when there are documents.
- Keep `U Upload document` available for admin users or allow backend to enforce permission.
- Do not duplicate `No documents found`.

## 4. Document Detail

```text
DOCUMENTS / DETAIL

bed_manual.pdf

+-------------+--------------------------+
| Field       | Value                    |
+-------------+--------------------------+
| Document ID | doc_1                    |
| Status      | ready                    |
| Pages       | 42                       |
| Updated     | 2026-05-14               |
+-------------+--------------------------+

> View structure
  Open page
  Retrieve from this document
  Reindex document
  Delete document
  Back

Up/Down Select | Enter Choose | B Back | Q Quit
```

## 5. Retrieval Input Screen

```text
RETRIEVAL

Ask a question against the document corpus.

Query:
  [ how do I reset the pendant?                                  ]

Mode:
  > auto
    semantic
    navigation
    hybrid

Top K:
  [ 5 ]

Document filter:
  none

> Run retrieval
  Generate answer
  Compare modes
  Back

Tab Next Field | Up/Down Select | Enter Choose | B Back | Q Quit
```

## 6. Retrieved Context Screen

```text
RETRIEVAL / CONTEXT

Query:
  how do I reset the pendant?

+-----+----------+-------------+-------+--------+---------------------+
| #   | Source   | Engine      | Score | Pages  | Section             |
+-----+----------+-------------+-------+--------+---------------------+
| > 1 | doc_123  | navigation  | 0.84  | 12     | Troubleshooting     |
|   2 | doc_456  | semantic    | 0.77  | 4      | Pendant Controls    |
|   3 | doc_123  | hybrid      | 0.72  | 14-15  | Controller Recovery |
+-----+----------+-------------+-------+--------+---------------------+

Selected Evidence [1]

Document:
  doc_123

Section:
  Troubleshooting

Text:
  To reset the pendant, disconnect power, wait 30 seconds, reconnect the
  power cable, and follow the pendant reset sequence.

Actions:
  Up/Down Select evidence
  Enter   Open source page
  A       Generate answer
  M       Change retrieval mode
  B       Back
  Q       Quit
```

## TDD Targets

```text
test_empty_documents_screen_shows_upload_refresh_back_quit
test_empty_documents_screen_does_not_show_enter_open
test_empty_documents_screen_does_not_duplicate_no_documents_found
test_documents_screen_with_documents_includes_upload_shortcut
test_documents_screen_shows_enter_open_only_when_documents_exist
test_retrieval_screen_renders_query_mode_top_k_and_actions
test_retrieved_context_screen_renders_evidence_table_and_selected_detail
```
