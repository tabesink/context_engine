# Upload Flow Screen Targets

These are the target ASCII screen views for the `context-engine` upload flow.

Use these as inspiration for implementation and tests.

## 1. Upload Document Form

```text
ADMIN DOCUMENTS / UPLOAD

Select a file to upload into the document corpus.

File path:
  [ C:\Users\admin\Documents\manual.pdf                         ]

Validation:
  File will be checked before upload.

> Submit upload
  Clear path
  Back
  Quit

Tab Next Field | Enter Choose | B Back | Q Quit
```

## 2. Upload Form With Missing Path Error

```text
ADMIN DOCUMENTS / UPLOAD

[ERROR] File not found

The file path below does not exist:

  C:\Users\admin\Documents\manual.pdf

File path:
  [ C:\Users\admin\Documents\manual.pdf                         ]

> Edit file path
  Back
  Quit

Enter Choose | B Back | Q Quit
```

## 3. Upload Complete With Local Job

```text
ADMIN DOCUMENTS / UPLOAD

[SUCCESS] Upload complete

Resume_2026_working.pdf was uploaded successfully.
An indexing job was created and is ready to inspect.

+-------------+--------------------------------------+
| Field       | Value                                |
+-------------+--------------------------------------+
| File        | Resume_2026_working.pdf              |
| Status      | uploaded                             |
| Document ID | 54d1d557...b7308d2905                |
| Job ID      | b40dc5e9...9f80ec50de48              |
+-------------+--------------------------------------+

Recommended next step:
> View job status
  Return to documents
  Upload another document
  Show full IDs
  Quit

Up/Down Select | Enter Choose | B Back | Q Quit
```

Implementation notes:

- Default selected action should be `View job status`.
- Use green for `[SUCCESS]`.
- Use yellow/admin accent for breadcrumb if desired.
- Truncate long IDs in the table.
- Full UUIDs should be available through `Show full IDs`.

## 4. Upload Complete With LightRAG Forwarding

```text
ADMIN DOCUMENTS / UPLOAD

[SUCCESS] Upload complete

Resume_2026_working.pdf was uploaded and forwarded to LightRAG.
No local indexing job was created.

+----------------+--------------------------------------+
| Field          | Value                                |
+----------------+--------------------------------------+
| File           | Resume_2026_working.pdf              |
| Status         | forwarded_to_lightrag                |
| Document ID    | 54d1d557...b7308d2905                |
| Local Job ID   | none                                 |
+----------------+--------------------------------------+

Recommended next step:
> Return to documents
  View LightRAG labels
  Upload another document
  Show full IDs
  Quit

Up/Down Select | Enter Choose | B Back | Q Quit
```

Implementation notes:

- Do not crash when `job_id` is null.
- Default selected action should be `Return to documents`.
- Offer `View LightRAG labels` if graph/label routes are available.

## 5. Upload Complete Full ID Details

```text
ADMIN DOCUMENTS / UPLOAD / DETAILS

Full identifiers

+-------------+--------------------------------------+
| Field       | Value                                |
+-------------+--------------------------------------+
| Document ID | 54d1d557-f9f1-41b9-9776-b9b7308d2905 |
| Job ID      | b40dc5e9-b05b-481e-a8ef-9f80ec50de48 |
+-------------+--------------------------------------+

> Back to upload result
  Copy document ID
  Copy job ID
  Quit

Up/Down Select | Enter Choose | B Back | Q Quit
```

If clipboard support is not available, omit copy actions and just show full IDs.

## 6. Upload Forbidden

```text
ADMIN DOCUMENTS / UPLOAD

[ERROR] Forbidden

The backend rejected this upload request.

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

Implementation notes:

- Do not infer admin status locally.
- Attempt the backend request and render backend `403`.
- Do not print token, password, or request headers.

## 7. Upload Connection Failure

```text
ADMIN DOCUMENTS / UPLOAD

[ERROR] Upload failed

Could not connect to backend.

Backend:
  http://127.0.0.1:8010

> Retry upload
  Edit file path
  Back
  Quit

Up/Down Select | Enter Choose | B Back | Q Quit
```

## TDD Targets

```text
test_upload_result_screen_does_not_show_stale_startup_output
test_upload_success_defaults_to_view_job_status_when_job_exists
test_upload_success_without_job_defaults_to_return_documents
test_upload_result_truncates_long_document_and_job_ids
test_upload_result_uses_compact_footer
test_upload_result_view_job_status_opens_job_screen
test_upload_result_return_to_documents_opens_documents_screen
test_upload_result_upload_another_opens_upload_form
test_upload_forbidden_renders_backend_403
```
