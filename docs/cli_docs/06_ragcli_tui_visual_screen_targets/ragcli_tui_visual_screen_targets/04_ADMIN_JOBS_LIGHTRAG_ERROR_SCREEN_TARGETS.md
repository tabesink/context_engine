# Admin, Jobs, LightRAG, and Error Screen Targets

These screens support admin workflows, job inspection, graph exploration, and errors.

## 1. Job Status After Upload

```text
JOBS / STATUS

[WARN] Indexing in progress

+-------------+--------------------------------------+
| Field       | Value                                |
+-------------+--------------------------------------+
| Job ID      | b40dc5e9...9f80ec50de48              |
| Type        | index_document                       |
| Status      | running                              |
| Document ID | 54d1d557...b7308d2905                |
| Started     | 2026-05-14 20:41                     |
+-------------+--------------------------------------+

Progress:
  Parsing document and building retrieval index.

> Refresh status
  Return to documents
  Back
  Quit

Enter Choose | Ctrl+R Refresh | B Back | Q Quit
```

## 2. Job Failed

```text
JOBS / STATUS

[ERROR] Job failed

+-------------+--------------------------------------+
| Field       | Value                                |
+-------------+--------------------------------------+
| Job ID      | b40dc5e9...9f80ec50de48              |
| Type        | index_document                       |
| Status      | failed                               |
| Document ID | 54d1d557...b7308d2905                |
+-------------+--------------------------------------+

Error:
  Could not parse document. The file may be corrupted or unsupported.

Recommended next step:
> Retry job
  Upload another document
  Return to documents
  Quit

Up/Down Select | Enter Choose | B Back | Q Quit
```

## 3. LightRAG Labels

```text
LIGHTRAG / LABELS

+-----+------------------------+-------+
| #   | Label                  | Count |
+-----+------------------------+-------+
| > 1 | installation           | 42    |
|   2 | reset                  | 35    |
|   3 | pendant                | 28    |
|   4 | controller             | 24    |
|   5 | troubleshooting        | 21    |
+-----+------------------------+-------+

Selected:
  installation

> Open graph
  Search labels
  Refresh
  Back
  Quit

Up/Down Select | Enter Choose | Ctrl+R Refresh | B Back | Q Quit
```

## 4. LightRAG Disabled

```text
LIGHTRAG

[ERROR] LightRAG unavailable

The backend returned:

  LightRAG is disabled.

This CLI does not connect to LightRAG directly.
Enable LightRAG in the backend configuration, then refresh.

> Refresh
  Back
  Quit

Up/Down Select | Enter Choose | B Back | Q Quit
```

## 5. Backend Gaps

```text
BACKEND GAPS

These capabilities are planned but do not have backend routes yet.

+----------------+-------------------------------+--------------------------+
| Capability     | CLI Command                   | Status                   |
+----------------+-------------------------------+--------------------------+
| Chat           | ragcli chat                   | not_supported_by_backend |
| Users          | ragcli users list             | not_supported_by_backend |
| Conversations  | ragcli conversations list     | not_supported_by_backend |
| Runs           | ragcli runs status            | not_supported_by_backend |
| Approvals      | ragcli runs approvals list    | not_supported_by_backend |
+----------------+-------------------------------+--------------------------+

> View command details
  Back
  Quit

Up/Down Select | Enter Choose | B Back | Q Quit
```

## 6. Forbidden / Admin Required

```text
ADMIN DOCUMENTS

[ERROR] Forbidden

The backend rejected this request.

+--------+----------------------------+
| Field  | Value                      |
+--------+----------------------------+
| Code   | forbidden                  |
| Status | 403                        |
| Reason | Admin permission required  |
+--------+----------------------------+

> Back
  Quit

Up/Down Select | Enter Choose | B Back | Q Quit
```

## 7. Connection Failure

```text
CONNECTION FAILED

[ERROR] Could not connect to backend

Backend:
  http://127.0.0.1:8010

Try:
  1. Confirm the backend is running.
  2. Check the API base URL.
  3. Restart the CLI after the backend is available.

> Retry
  Change API URL
  Quit

Up/Down Select | Enter Choose | Q Quit
```

## 8. Loading Screen

```text
LOADING

Fetching documents...

Backend:
  http://127.0.0.1:8010

Please wait.
```

## 9. Login Screen

```text
CONTEXT ENGINE LOGIN

Backend:
  http://127.0.0.1:8010

Email:
  [ admin@example.com                                             ]

Password:
  [ ********                                                     ]

> Login
  Change backend URL
  Quit

Tab Next Field | Enter Choose | Q Quit
```

## 10. Logged Out Screen

```text
LOGGED OUT

Your local CLI session has been cleared.

> Login again
  Quit

Up/Down Select | Enter Choose | Q Quit
```

## TDD Targets

```text
test_job_status_running_shows_warning_and_refresh_action
test_job_failed_shows_retry_as_default_action
test_lightrag_labels_screen_uses_ascii_table
test_lightrag_disabled_renders_backend_error
test_backend_gaps_screen_lists_not_supported_commands
test_forbidden_screen_renders_backend_403
test_connection_failure_screen_suggests_retry_and_change_api_url
test_login_screen_masks_password
test_logged_out_screen_offers_login_again
```
