# Phase 4 TDD Plan: Guided Flows and Frontend Traceability

## Objective

Add a small number of guided one-shot workflows that test future frontend behavior while still calling real backend routes.

Guided flows should be useful, not decorative.

## Candidate commands

```bash
ragcli retrieval compare --query "reset procedure"
ragcli admin documents upload-flow --file ./manual.pdf
ragcli admin dashboard
ragcli screen documents
ragcli screen retrieval
ragcli screen graph
ragcli screen admin
```

## Rule

A flow may call multiple backend routes, but it must not invent backend behavior.

If a route is missing, return a visible backend-gap message.

## Target modules

```text
cli/flows/
  retrieval_compare.py
  upload_document.py
  admin_dashboard.py

cli/commands/
  flows.py
  screens.py
```

## Flow 1 — Retrieval compare

### User story

As a developer/admin, I want to compare retrieval modes for the same query so I can understand how `auto`, `semantic`, `navigation`, and `hybrid` behave.

### Command

```bash
ragcli retrieval compare --query "reset procedure" --top-k 5
```

### Backend calls

```text
POST /query/retrieve mode=auto
POST /query/retrieve mode=semantic
POST /query/retrieve mode=navigation
POST /query/retrieve mode=hybrid
```

### Human output

```text
RETRIEVAL MODE COMPARISON

Query: reset procedure
Top K: 5

+------------+----------+--------------+----------------+
| Mode       | Evidence | Top Score    | Selected Engine|
+------------+----------+--------------+----------------+
| auto       | 5        | 0.83         | navigation     |
| semantic   | 5        | 0.78         | semantic       |
| navigation | 5        | 0.83         | navigation     |
| hybrid     | 5        | 0.81         | hybrid         |
+------------+----------+--------------+----------------+
```

### TDD slices

1. Command exists.
2. Calls all four modes.
3. Renders ASCII comparison table.
4. Handles one mode failure without hiding other results.
5. JSON output returns stable comparison shape if supported.

### Tests

```text
test_retrieval_compare_calls_all_supported_modes
test_retrieval_compare_human_output_uses_ascii_table
test_retrieval_compare_handles_partial_mode_failure
test_retrieval_compare_json_output_is_stable
```

---

## Flow 2 — Admin upload flow

### User story

As an admin, I want one upload workflow that uploads a file and tells me the next indexing/job step.

### Command

```bash
ragcli admin documents upload-flow --file ./manual.pdf
```

### Backend calls

Minimum:

```text
POST /admin/documents/upload
```

Optional if response has `job_id`:

```text
GET /jobs/{job_id}
```

### Human output

```text
UPLOAD FLOW

File: manual.pdf
Document: doc_123
Status: uploaded

Indexing job:
  job_456 pending

Next:
  ragcli jobs status --job-id job_456
```

### TDD slices

1. Local missing file returns local CLI error.
2. Upload success with local job renders job next step.
3. Upload success with LightRAG forwarding and no job does not crash.
4. Backend 403 is rendered as backend error.
5. No token/password printed.

### Tests

```text
test_upload_flow_missing_file_returns_local_error
test_upload_flow_success_with_job_suggests_job_status
test_upload_flow_success_without_job_handles_lightrag_metadata
test_upload_flow_backend_403_is_rendered
test_upload_flow_does_not_print_secrets
```

---

## Flow 3 — Admin dashboard

### User story

As an admin, I want a single summary of corpus, jobs, and query logs.

### Command

```bash
ragcli admin dashboard
```

### Backend calls

```text
GET /admin/documents
GET /jobs
GET /admin/query-logs
```

### Human output

```text
ADMIN DASHBOARD

Documents:
  ready: 12
  processing: 2
  failed: 1

Jobs:
  pending: 1
  failed: 1

Recent queries:
+----------+-------------+--------+
| Time     | User        | Mode   |
+----------+-------------+--------+
| 10:41 AM | user@x.com  | hybrid |
+----------+-------------+--------+
```

### TDD slices

1. Command exists.
2. Calls expected admin routes.
3. Renders dashboard summary.
4. Handles 403 from backend.
5. Handles partial route failure gracefully if desired.

### Tests

```text
test_admin_dashboard_calls_documents_jobs_and_query_logs
test_admin_dashboard_human_output_shows_summary_counts
test_admin_dashboard_backend_403_is_rendered
```

---

## Flow 4 — Screen aliases

### User story

As a developer, I want quick frontend-like screen aliases.

### Commands

```bash
ragcli screen documents
ragcli screen retrieval
ragcli screen graph
ragcli screen admin
```

### TDD slices

1. `screen documents` calls `GET /documents`.
2. `screen graph` calls label/popular or gap-safe graph summary.
3. `screen admin` calls admin dashboard routes.
4. JSON behavior is either disabled with clear error or uses stable shape.

### Tests

```text
test_screen_documents_renders_document_library
test_screen_admin_renders_backend_403_for_non_admin
test_screen_graph_renders_lightrag_summary_or_disabled_error
```

## Frontend traceability docs

Add:

```text
docs/cli_docs/frontend_traceability.md
```

Suggested structure:

```markdown
# Frontend Traceability Matrix

| Frontend Screen | CLI/TUI Equivalent | Backend Routes | Status | Gaps |
|---|---|---|---|---|
```

Also add:

```text
docs/cli_docs/tui_ux.md
docs/cli_docs/tdd_implementation_status.md
```

## Acceptance criteria

- Guided flows compose existing backend APIs.
- Flow tests use public CLI behavior.
- No flow bypasses backend authorization.
- No flow calls LightRAG directly.
- Backend gaps remain explicit.
- Human output remains ASCII/monochrome.
- JSON remains stable or explicitly unsupported for flows.
