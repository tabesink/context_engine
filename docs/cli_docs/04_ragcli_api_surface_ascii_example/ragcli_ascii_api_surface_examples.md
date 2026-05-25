# context-engine ASCII Human Output Examples For All CLI/API Surfaces

> **Product note:** Install **`context-engine`** / **`context-tui`** to open the Rich interactive UI (**`cli.launcher:main`**). Prompt lines such as **`$ context-engine documents list`** label the *underlying capability / REST shape* retained from earlier Typer experiments—they are **not** valid standalone shell commands today.

This document shows proposed human-mode CLI output examples for the full **`context-engine` surface**.

Design rules:

- Use ASCII tables only.
- Keep output mostly black and white.
- Use color only in the actual terminal for semantic status, not in the text examples here.
- Keep JSON output separate and stable.
- Human output may be improved for readability.
- The terminal client must remain API-first and route-mirrored.
- Planned/backend-gap commands must return `not_supported_by_backend`.

---

# 1. Session / Auth Surfaces

## 1.1 Login

Command:

```bash
context-engine login --email admin@example.com
```

Example human output:

```text
LOGIN

Backend:
  http://127.0.0.1:8000

Email:
  admin@example.com

Status:
  success

Saved session:
+----------------+---------------------------+
| Field          | Value                     |
+----------------+---------------------------+
| API base URL   | http://127.0.0.1:8000     |
| Token stored   | yes                       |
| Password saved | no                        |
+----------------+---------------------------+

Next:
  context-engine auth me
  context-engine documents list
```

Failed login:

```text
LOGIN FAILED

auth_failed: Invalid email or password.

Next:
  context-engine login --email admin@example.com
```

Security note:

```text
The access token is stored locally and is never printed.
The password is never stored.
```

---

## 1.2 Auth Me

Command:

```bash
context-engine auth me
```

Example human output:

```text
CURRENT SESSION

Backend:
  http://127.0.0.1:8000

User:
+----------------+---------------------------+
| Field          | Value                     |
+----------------+---------------------------+
| Email          | admin@example.com         |
| Role           | admin                     |
| Authenticated  | true                      |
+----------------+---------------------------+

Next:
  context-engine documents list
  context-engine admin documents list
```

If not logged in:

```text
AUTH REQUIRED

auth_required: Run `context-engine login` first.

Next:
  context-engine login --email admin@example.com
```

---

## 1.3 Logout

Command:

```bash
context-engine logout
```

Example human output:

```text
LOGOUT

Status:
  local session cleared

Cleared:
+----------------+-------+
| Item           | State |
+----------------+-------+
| API base URL   | yes   |
| Access token   | yes   |
| Password       | n/a   |
+----------------+-------+

Next:
  context-engine login --email admin@example.com
```

---

# 2. Documents And Retrieval Surfaces

## 2.1 Documents List

Command:

```bash
context-engine documents list
```

Example human output:

```text
DOCUMENTS

Backend:
  http://127.0.0.1:8000

+---------+----------------------+----------+-------+------------+
| ID      | Filename             | Status   | Pages | Updated    |
+---------+----------------------+----------+-------+------------+
| doc_123 | bed_manual.pdf       | ready    | 42    | 2026-05-14 |
| doc_456 | mattress_specs.pdf   | ready    | 18    | 2026-05-13 |
| doc_789 | service_guide.pdf    | indexing | --    | 2026-05-14 |
+---------+----------------------+----------+-------+------------+

Next:
  context-engine documents show --document-id doc_123
  context-engine documents retrieve --query "reset procedure" --document-id doc_123
```

Empty state:

```text
DOCUMENTS

No documents found.

Next:
  context-engine admin documents upload --file ./manual.pdf
```

---

## 2.2 Documents Show

Command:

```bash
context-engine documents show --document-id doc_123
```

Example human output:

```text
DOCUMENT DETAIL

+----------------+----------------------------+
| Field          | Value                      |
+----------------+----------------------------+
| Document ID    | doc_123                    |
| Filename       | bed_manual.pdf             |
| Status         | ready                      |
| Pages          | 42                         |
| Created        | 2026-05-13 09:41           |
| Updated        | 2026-05-14 10:22           |
+----------------+----------------------------+

Available actions:
  context-engine documents structure --document-id doc_123
  context-engine documents page --document-id doc_123 --page-number 1
  context-engine documents retrieve --query "your question" --document-id doc_123
```

Not found:

```text
DOCUMENT NOT FOUND

not_found: Document `doc_missing` was not found.

Next:
  context-engine documents list
```

---

## 2.3 Documents Structure

Command:

```bash
context-engine documents structure --document-id doc_123
```

Example human output:

```text
DOCUMENT STRUCTURE

Document:
  doc_123

+-------+-----------------------------+-------------+
| Level | Title                       | Pages       |
+-------+-----------------------------+-------------+
| 1     | Introduction                | 1-2         |
| 1     | Installation                | 3-8         |
| 2     | Electrical Setup            | 5-6         |
| 2     | Pendant Connection          | 7-8         |
| 1     | Troubleshooting             | 12-17       |
| 2     | Pendant Reset               | 13          |
| 2     | Controller Recovery         | 14-15       |
+-------+-----------------------------+-------------+

Next:
  context-engine documents page --document-id doc_123 --page-number 13
  context-engine documents retrieve --query "Pendant Reset" --document-id doc_123
```

---

## 2.4 Documents Page

Command:

```bash
context-engine documents page --document-id doc_123 --page-number 13
```

Example human output:

```text
DOCUMENT PAGE

+----------------+----------------------------+
| Field          | Value                      |
+----------------+----------------------------+
| Document ID    | doc_123                    |
| Filename       | bed_manual.pdf             |
| Page           | 13                         |
| Section        | Pendant Reset              |
+----------------+----------------------------+

Content:
  If the pendant does not respond, verify that the cable is seated correctly.
  Disconnect the bed from power, wait 30 seconds, reconnect the power cable,
  and perform the reset sequence using the pendant controls.

Next:
  context-engine documents page --document-id doc_123 --page-number 12
  context-engine documents page --document-id doc_123 --page-number 14
  context-engine documents retrieve --query "pendant reset" --document-id doc_123
```

---

## 2.5 Documents Retrieve

Command:

```bash
context-engine documents retrieve --query "how do I reset the pendant?" --mode hybrid --top-k 3 --document-id doc_123
```

Example human output:

```text
RETRIEVED CONTEXT

Query:
  how do I reset the pendant?

Request:
+------------------------+-------------------------------+
| Field                  | Value                         |
+------------------------+-------------------------------+
| Requested mode         | hybrid                        |
| Top K                  | 3                             |
| Document filter        | doc_123                       |
| General fallback       | false                         |
| Debug requested        | false                         |
+------------------------+-------------------------------+

Results:
+-----+----------+-------------+-------+--------+---------------------+
| #   | Source   | Engine      | Score | Pages  | Section             |
+-----+----------+-------------+-------+--------+---------------------+
| 1   | doc_123  | navigation  | 0.84  | 12     | Troubleshooting     |
| 2   | doc_123  | semantic    | 0.79  | 13     | Pendant Reset       |
| 3   | doc_123  | hybrid      | 0.74  | 14-15  | Controller Recovery |
+-----+----------+-------------+-------+--------+---------------------+

Evidence [1]
+----------------+-----------------------------------------+
| Evidence ID    | nav-1                                   |
| Document       | doc_123                                 |
| Source engine  | navigation                              |
| Score          | 0.84                                    |
| Page           | 12                                      |
| Section        | Troubleshooting                         |
+----------------+-----------------------------------------+

Text:
  To reset the pendant, disconnect the bed from power, wait 30 seconds,
  reconnect the power cable, and press the pendant reset sequence described
  in the troubleshooting section.

Evidence [2]
+----------------+-----------------------------------------+
| Evidence ID    | sem-2                                   |
| Document       | doc_123                                 |
| Source engine  | semantic                                |
| Score          | 0.79                                    |
| Page           | 13                                      |
| Section        | Pendant Reset                           |
+----------------+-----------------------------------------+

Text:
  If the pendant does not respond, verify that the cable is seated correctly.
  Then perform the reset procedure using the pendant control buttons.

Evidence [3]
+----------------+-----------------------------------------+
| Evidence ID    | hyb-3                                   |
| Document       | doc_123                                 |
| Source engine  | hybrid                                  |
| Score          | 0.74                                    |
| Pages          | 14-15                                   |
| Section        | Controller Recovery                     |
+----------------+-----------------------------------------+

Text:
  Controller recovery may be required when both pendant and motor functions
  are unresponsive. Follow the reset and power-cycle sequence before replacing
  the controller.

Next:
  context-engine documents answer --query "how do I reset the pendant?" --document-id doc_123
  context-engine documents page --document-id doc_123 --page-number 12
  context-engine documents retrieve --query "how do I reset the pendant?" --mode semantic --top-k 5
```

---

## 2.6 Documents Retrieve With Admin Debug

Command:

```bash
context-engine documents retrieve --query "installation steps" --mode auto --top-k 3 --include-debug
```

Example human output:

```text
RETRIEVED CONTEXT

Query:
  installation steps

Request:
+------------------------+-------------------------------+
| Field                  | Value                         |
+------------------------+-------------------------------+
| Requested mode         | auto                          |
| Top K                  | 3                             |
| Document filter        | none                          |
| General fallback       | false                         |
| Debug requested        | true                          |
+------------------------+-------------------------------+

Results:
+-----+----------+-------------+-------+-------+------------------+
| #   | Source   | Engine      | Score | Pages | Section          |
+-----+----------+-------------+-------+-------+------------------+
| 1   | doc_123  | navigation  | 0.88  | 3-4   | Installation     |
| 2   | doc_456  | semantic    | 0.81  | 2     | Setup Checklist  |
| 3   | doc_123  | hybrid      | 0.76  | 5     | Electrical Setup |
+-----+----------+-------------+-------+-------+------------------+

Debug:
+------------------------+-------------------------------+
| Field                  | Value                         |
+------------------------+-------------------------------+
| Requested mode         | auto                          |
| Selected engine        | navigation                    |
| Candidate engines      | semantic, navigation, hybrid  |
| Final evidence count   | 3                             |
+------------------------+-------------------------------+
```

For non-admin users, the debug section is omitted even when `--include-debug` is sent.

---

## 2.7 Documents Answer

Command:

```bash
context-engine documents answer --query "how do I reset the pendant?" --document-id doc_123
```

Example human output:

```text
ANSWER

Question:
  how do I reset the pendant?

Answer:
  To reset the pendant, first confirm the pendant cable is fully seated.
  Then disconnect the bed from power, wait 30 seconds, reconnect the bed,
  and perform the reset sequence described in the troubleshooting section.
  If the pendant and motors remain unresponsive, follow the controller
  recovery procedure.

Sources:
+-----+----------+-------+---------------------+-------+
| #   | Document | Pages | Section             | Score |
+-----+----------+-------+---------------------+-------+
| 1   | doc_123  | 12    | Troubleshooting     | 0.84  |
| 2   | doc_123  | 13    | Pendant Reset       | 0.79  |
| 3   | doc_123  | 14-15 | Controller Recovery | 0.74  |
+-----+----------+-------+---------------------+-------+

Next:
  context-engine documents page --document-id doc_123 --page-number 12
  context-engine documents retrieve --query "how do I reset the pendant?" --document-id doc_123
```

---

## 2.8 Top-Level Query

Command:

```bash
context-engine query --query "what does the manual say about reset?"
```

Example human output:

```text
QUERY ANSWER

Question:
  what does the manual say about reset?

Answer:
  The manual says reset should begin with basic connection checks, followed
  by a power cycle. If pendant controls remain unresponsive, the controller
  recovery procedure should be followed.

Sources:
+-----+----------+-------+---------------------+
| #   | Document | Pages | Section             |
+-----+----------+-------+---------------------+
| 1   | doc_123  | 12    | Troubleshooting     |
| 2   | doc_123  | 13    | Pendant Reset       |
+-----+----------+-------+---------------------+

Next:
  context-engine documents retrieve --query "what does the manual say about reset?"
```

---

## 2.9 Documents Content Backend Gap

Command:

```bash
context-engine documents content --document-id doc_123 --pages 1-3
```

Example human output:

```text
BACKEND GAP

not_supported_by_backend: `context-engine documents content --pages 1-3` needs a backend route first.

Reason:
+----------------+---------------------------------------------+
| Field          | Value                                       |
+----------------+---------------------------------------------+
| Capability     | page range content                          |
| Current route  | none                                        |
| Suggested API  | GET /documents/{document_id}/content?pages= |
+----------------+---------------------------------------------+

Available today:
  context-engine documents page --document-id doc_123 --page-number 1
```

---

## 2.10 Documents Search Backend Gap

Command:

```bash
context-engine documents search --query "reset"
```

Example human output:

```text
BACKEND GAP

not_supported_by_backend: `context-engine documents search` needs a backend route first.

Reason:
+----------------+--------------------------------+
| Field          | Value                          |
+----------------+--------------------------------+
| Capability     | document text search           |
| Current route  | none                           |
| Suggested API  | GET /documents/search?q=reset  |
+----------------+--------------------------------+

Available today:
  context-engine documents retrieve --query "reset"
```

---

# 3. LightRAG Graph Surfaces

## 3.1 LightRAG Labels List

Command:

```bash
context-engine lightrag labels list
```

Example human output:

```text
LIGHTRAG LABELS

+-----+------------------------+
| #   | Label                  |
+-----+------------------------+
| 1   | installation           |
| 2   | pendant reset          |
| 3   | controller recovery    |
| 4   | troubleshooting        |
| 5   | electrical setup       |
+-----+------------------------+

Next:
  context-engine lightrag labels search --query "reset"
  context-engine lightrag graphs show --label "pendant reset"
```

---

## 3.2 LightRAG Popular Labels

Command:

```bash
context-engine lightrag labels popular --limit 10
```

Example human output:

```text
POPULAR LIGHTRAG LABELS

+-----+------------------------+-------+
| #   | Label                  | Count |
+-----+------------------------+-------+
| 1   | installation           | 42    |
| 2   | reset                  | 35    |
| 3   | pendant                | 28    |
| 4   | controller             | 24    |
| 5   | troubleshooting        | 21    |
+-----+------------------------+-------+

Next:
  context-engine lightrag graphs show --label "installation"
```

---

## 3.3 LightRAG Labels Search

Command:

```bash
context-engine lightrag labels search --query "reset" --limit 5
```

Example human output:

```text
LIGHTRAG LABEL SEARCH

Query:
  reset

+-----+------------------------+-------+
| #   | Label                  | Score |
+-----+------------------------+-------+
| 1   | reset                  | 1.00  |
| 2   | pendant reset          | 0.92  |
| 3   | controller reset       | 0.84  |
| 4   | reset sequence         | 0.78  |
| 5   | power cycle reset      | 0.72  |
+-----+------------------------+-------+

Next:
  context-engine lightrag graphs show --label "pendant reset"
```

---

## 3.4 LightRAG Graph Show

Command:

```bash
context-engine lightrag graphs show --label "pendant reset" --max-depth 2 --max-nodes 100
```

Example human output:

```text
LIGHTRAG GRAPH

Label:
  pendant reset

Request:
+----------------+----------------+
| Field          | Value          |
+----------------+----------------+
| Max depth      | 2              |
| Max nodes      | 100            |
+----------------+----------------+

Summary:
+----------------+----------------+
| Field          | Value          |
+----------------+----------------+
| Nodes          | 37             |
| Edges          | 52             |
| Depth returned | 2              |
+----------------+----------------+

Top connected labels:
+-----+------------------------+-------------+
| #   | Label                  | Relationship|
+-----+------------------------+-------------+
| 1   | pendant                | related_to  |
| 2   | controller             | connected_to|
| 3   | power cycle            | prerequisite|
| 4   | troubleshooting        | section_of  |
+-----+------------------------+-------------+

Note:
  Use JSON output for frontend graph visualization.

Next:
  context-engine lightrag graphs show --label "pendant reset" --output json
```

---

## 3.5 LightRAG Disabled Error

Command:

```bash
context-engine lightrag labels popular
```

Example human output:

```text
LIGHTRAG UNAVAILABLE

lightrag_disabled: LightRAG is disabled.

Reason:
  The backend returned a disabled-service response.

Next:
  Enable LIGHTRAG_ENABLED=true in the backend environment.
  Confirm the backend can reach the configured LightRAG service.
```

---

# 4. Admin Document Surfaces

## 4.1 Admin Documents Upload

Command:

```bash
context-engine admin documents upload --file ./manual.pdf
```

Example human output when local indexing job is created:

```text
ADMIN DOCUMENT UPLOAD

File:
  ./manual.pdf

Upload result:
+----------------+----------------------------+
| Field          | Value                      |
+----------------+----------------------------+
| Document ID    | doc_123                    |
| Filename       | manual.pdf                 |
| Status         | uploaded                   |
| Job ID         | job_456                    |
+----------------+----------------------------+

Next:
  context-engine jobs status --job-id job_456
  context-engine admin documents reingest --document-id doc_123
```

Example human output when LightRAG forwarding is enabled:

```text
ADMIN DOCUMENT UPLOAD

File:
  ./manual.pdf

Upload result:
+------------------------+----------------------------+
| Field                  | Value                      |
+------------------------+----------------------------+
| Document ID            | doc_123                    |
| Filename               | manual.pdf                 |
| Status                 | forwarded_to_lightrag      |
| Local job ID           | none                       |
| LightRAG remote status | accepted                   |
+------------------------+----------------------------+

Next:
  context-engine admin documents list
  context-engine lightrag labels popular
```

---

## 4.2 Admin Documents List

Command:

```bash
context-engine admin documents list
```

Example human output:

```text
ADMIN DOCUMENTS

+---------+----------------------+----------+-------------+------------+
| ID      | Filename             | Status   | Indexed By  | Updated    |
+---------+----------------------+----------+-------------+------------+
| doc_123 | bed_manual.pdf       | ready    | local       | 2026-05-14 |
| doc_456 | mattress_specs.pdf   | ready    | lightrag    | 2026-05-13 |
| doc_789 | service_guide.pdf    | failed   | local       | 2026-05-14 |
+---------+----------------------+----------+-------------+------------+

Admin actions:
  context-engine admin documents reingest --document-id doc_789
  context-engine admin documents refresh-status --document-id doc_123
  context-engine admin documents delete --document-id doc_789
```

---

## 4.3 Admin Documents Reingest

Command:

```bash
context-engine admin documents reingest --document-id doc_123
```

Example human output:

```text
ADMIN DOCUMENT REINGEST

Request:
+----------------+----------------------------+
| Field          | Value                      |
+----------------+----------------------------+
| Document ID    | doc_123                    |
| Action         | reingest                      |
+----------------+----------------------------+

Result:
+----------------+----------------------------+
| Field          | Value                      |
+----------------+----------------------------+
| Status         | accepted                   |
| Job ID         | job_456                    |
+----------------+----------------------------+

Next:
  context-engine jobs status --job-id job_456
```

---

## 4.4 Admin Documents Refresh Status

Command:

```bash
context-engine admin documents refresh-status --document-id doc_123
```

Example human output:

```text
ADMIN DOCUMENT REFRESH STATUS

Request:
+----------------+----------------------------+
| Field          | Value                      |
+----------------+----------------------------+
| Document ID    | doc_123                    |
| Action         | refresh-status                    |
+----------------+----------------------------+

Result:
+----------------+----------------------------+
| Field          | Value                      |
+----------------+----------------------------+
| Status         | accepted                   |
| Job ID         | job_789                    |
+----------------+----------------------------+

Next:
  context-engine jobs status --job-id job_789
```

---

## 4.5 Admin Documents Delete

Command:

```bash
context-engine admin documents delete --document-id doc_789
```

Example human output:

```text
ADMIN DOCUMENT DELETE

Deleted:
+----------------+----------------------------+
| Field          | Value                      |
+----------------+----------------------------+
| Document ID    | doc_789                    |
| Filename       | service_guide.pdf          |
| Status         | deleted                    |
+----------------+----------------------------+

Next:
  context-engine admin documents list
```

---

## 4.6 Admin 403 Error

Command:

```bash
context-engine admin documents list
```

Example human output for normal user:

```text
FORBIDDEN

forbidden: Admin permission required.

Reason:
  The backend rejected this request.

Next:
  context-engine auth me
```

The CLI should not infer admin permissions locally. It should send the request and render the backend response.

---

## 4.7 Admin Corpus Publish Backend Gap

Command:

```bash
context-engine admin corpus publish
```

Example human output:

```text
BACKEND GAP

not_supported_by_backend: `context-engine admin corpus publish` needs a backend route first.

+----------------+---------------------------------------+
| Field          | Value                                 |
+----------------+---------------------------------------+
| Capability     | corpus version publish                |
| Current route  | none                                  |
| Suggested API  | POST /admin/corpus/publish            |
+----------------+---------------------------------------+
```

Same pattern for:

```bash
context-engine admin corpus rollback
context-engine admin corpus cleanup
```

---

# 5. Admin Observability Surfaces

## 5.1 Admin Audit Logs List

Command:

```bash
context-engine admin audit-logs list
```

Example human output:

```text
AUDIT LOGS

+---------------------+-------------------+----------------------+----------+
| Time                | User              | Action               | Status   |
+---------------------+-------------------+----------------------+----------+
| 2026-05-14 10:41:22 | admin@example.com | document.upload      | success  |
| 2026-05-14 10:43:10 | admin@example.com | document.refresh_status     | accepted |
| 2026-05-14 10:44:02 | user@example.com  | admin.documents.list | denied   |
+---------------------+-------------------+----------------------+----------+

Next:
  context-engine admin query-logs list
```

---

## 5.2 Admin Query Logs List

Command:

```bash
context-engine admin query-logs list
```

Example human output:

```text
QUERY LOGS

+---------------------+------------------+------------+-------+---------------------------+
| Time                | User             | Mode       | Top K | Query                     |
+---------------------+------------------+------------+-------+---------------------------+
| 2026-05-14 10:47:01 | user@example.com | hybrid     | 5     | reset procedure           |
| 2026-05-14 10:48:12 | user@example.com | semantic   | 3     | installation steps        |
| 2026-05-14 10:49:30 | admin@example... | navigation | 5     | controller recovery       |
+---------------------+------------------+------------+-------+---------------------------+

Next:
  context-engine documents retrieve --query "reset procedure" --include-debug
```

---

# 6. Job Surfaces

## 6.1 Jobs List

Command:

```bash
context-engine jobs list
```

Example human output:

```text
JOBS

+---------+----------------+----------+----------+---------------------+
| Job ID  | Type           | Status   | Document | Updated             |
+---------+----------------+----------+----------+---------------------+
| job_456 | document_ingest | running  | doc_123  | 2026-05-14 10:50:02 |
| job_789 | refresh-status        | failed   | doc_789  | 2026-05-14 10:44:19 |
| job_321 | upload_parse   | complete | doc_456  | 2026-05-14 09:30:10 |
+---------+----------------+----------+----------+---------------------+

Next:
  context-engine jobs status --job-id job_456
  context-engine jobs retry --job-id job_789
```

---

## 6.2 Jobs Status

Command:

```bash
context-engine jobs status --job-id job_789
```

Example human output:

```text
JOB STATUS

+----------------+----------------------------+
| Field          | Value                      |
+----------------+----------------------------+
| Job ID         | job_789                    |
| Type           | refresh-status                    |
| Status         | failed                     |
| Document ID    | doc_789                    |
| Created        | 2026-05-14 10:40:00        |
| Updated        | 2026-05-14 10:44:19        |
+----------------+----------------------------+

Error:
  Could not parse document. The file appears to be corrupted.

Next:
  context-engine jobs retry --job-id job_789
  context-engine admin documents delete --document-id doc_789
```

Successful job:

```text
JOB STATUS

+----------------+----------------------------+
| Field          | Value                      |
+----------------+----------------------------+
| Job ID         | job_321                    |
| Type           | upload_parse               |
| Status         | complete                   |
| Document ID    | doc_456                    |
+----------------+----------------------------+

Result:
  Document parsed and indexed successfully.

Next:
  context-engine documents show --document-id doc_456
```

---

## 6.3 Jobs Retry

Command:

```bash
context-engine jobs retry --job-id job_789
```

Example human output:

```text
JOB RETRY

Request:
+----------------+----------------------------+
| Field          | Value                      |
+----------------+----------------------------+
| Previous Job   | job_789                    |
| Action         | retry                      |
+----------------+----------------------------+

Result:
+----------------+----------------------------+
| Field          | Value                      |
+----------------+----------------------------+
| Status         | accepted                   |
| New Job ID     | job_790                    |
+----------------+----------------------------+

Next:
  context-engine jobs status --job-id job_790
```

---

# 7. Planned Surface Backend Gap Examples

The following commands are reserved CLI/API surfaces. Until backend routes exist, they should return `not_supported_by_backend`.

## 7.1 Users Create

Command:

```bash
context-engine users create --email user@example.com
```

Example human output:

```text
BACKEND GAP

not_supported_by_backend: `context-engine users create` needs a backend route first.

+----------------+-----------------------------+
| Field          | Value                       |
+----------------+-----------------------------+
| Capability     | user creation               |
| Current route  | none                        |
| Suggested API  | POST /users                 |
+----------------+-----------------------------+
```

---

## 7.2 Users List

Command:

```bash
context-engine users list
```

Example human output:

```text
BACKEND GAP

not_supported_by_backend: `context-engine users list` needs a backend route first.

+----------------+-----------------------------+
| Field          | Value                       |
+----------------+-----------------------------+
| Capability     | user listing                |
| Current route  | none                        |
| Suggested API  | GET /users                  |
+----------------+-----------------------------+
```

---

## 7.3 Retrievers List

Command:

```bash
context-engine retrievers list
```

Example human output:

```text
BACKEND GAP

not_supported_by_backend: `context-engine retrievers list` needs a backend route first.

+----------------+-----------------------------+
| Field          | Value                       |
+----------------+-----------------------------+
| Capability     | retriever registry          |
| Current route  | none                        |
| Suggested API  | GET /retrievers             |
+----------------+-----------------------------+
```

---

## 7.4 Agents List

Command:

```bash
context-engine agents list
```

Example human output:

```text
BACKEND GAP

not_supported_by_backend: `context-engine agents list` needs a backend route first.

+----------------+-----------------------------+
| Field          | Value                       |
+----------------+-----------------------------+
| Capability     | agent registry              |
| Current route  | none                        |
| Suggested API  | GET /agents                 |
+----------------+-----------------------------+
```

---

## 7.5 Conversations

Command:

```bash
context-engine conversations list
```

Example human output:

```text
BACKEND GAP

not_supported_by_backend: `context-engine conversations list` needs a backend route first.

+----------------+-----------------------------+
| Field          | Value                       |
+----------------+-----------------------------+
| Capability     | conversation history        |
| Current route  | none                        |
| Suggested API  | GET /conversations          |
+----------------+-----------------------------+
```

Same pattern for:

```bash
context-engine conversations create
context-engine conversations show --conversation-id CONV_ID
```

---

## 7.6 Chat

Command:

```bash
context-engine chat
```

Example human output:

```text
BACKEND GAP

not_supported_by_backend: `context-engine chat` needs a backend route first.

+----------------+-----------------------------+
| Field          | Value                       |
+----------------+-----------------------------+
| Capability     | interactive chat            |
| Current route  | none                        |
| Suggested API  | POST /chat or /messages     |
+----------------+-----------------------------+

Note:
  Do not fake chat locally in the CLI.
```

---

## 7.7 Messages

Command:

```bash
context-engine messages send --conversation-id conv_123 --content "hello"
```

Example human output:

```text
BACKEND GAP

not_supported_by_backend: `context-engine messages send` needs a backend route first.

+----------------+-----------------------------+
| Field          | Value                       |
+----------------+-----------------------------+
| Capability     | send conversation message   |
| Current route  | none                        |
| Suggested API  | POST /messages              |
+----------------+-----------------------------+
```

Same pattern for:

```bash
context-engine messages list --conversation-id conv_123
```

---

## 7.8 Runs

Command:

```bash
context-engine runs status --run-id run_123
```

Example human output:

```text
BACKEND GAP

not_supported_by_backend: `context-engine runs status` needs a backend route first.

+----------------+-----------------------------+
| Field          | Value                       |
+----------------+-----------------------------+
| Capability     | agent run status            |
| Current route  | none                        |
| Suggested API  | GET /runs/{run_id}          |
+----------------+-----------------------------+
```

Same pattern for:

```bash
context-engine runs cancel --run-id run_123
```

---

## 7.9 Run Approvals

Command:

```bash
context-engine runs approvals list
```

Example human output:

```text
BACKEND GAP

not_supported_by_backend: `context-engine runs approvals list` needs a backend route first.

+----------------+-----------------------------+
| Field          | Value                       |
+----------------+-----------------------------+
| Capability     | human approval queue        |
| Current route  | none                        |
| Suggested API  | GET /runs/approvals         |
+----------------+-----------------------------+
```

Same pattern for:

```bash
context-engine runs approvals approve --approval-id approval_123
context-engine runs approvals reject --approval-id approval_123
```

---

# 8. Common Error Examples

## 8.1 Auth Required

```text
AUTH REQUIRED

auth_required: Run `context-engine login` first.

Next:
  context-engine login --email admin@example.com
```

## 8.2 Connection Failure

```text
CONNECTION FAILED

connection_error: Could not connect to backend at http://127.0.0.1:8000.

Next:
  Start the backend:
    python -m uvicorn app.main:create_app --factory --reload

  Or pass a different backend:
    context-engine --api-base-url http://localhost:8000 auth me
```

## 8.3 Saved Session Base URL Warning

```text
warning: saved session uses a different --api-base-url; re-run login to switch
```

Then continue using the saved session URL.

## 8.4 Backend API Error

```text
API ERROR

invalid_request: document_id is required.

Status:
  400

Next:
  context-engine documents list
```

---

# 9. TUI Screen Example For Retrieved Context

Inside `context-engine`, the retrieved context screen should replace the previous screen.

```text
RETRIEVED CONTEXT

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
  Up/Down  Select evidence
  Enter    Open source page
  A        Generate answer
  M        Change retrieval mode
  B        Back
  Q        Quit
```

---

# 10. General Output Rules For Implementation

## Human mode

Human output should:

- use screen titles
- use compact ASCII tables
- show next useful commands
- show short actionable errors
- never print tokens/passwords
- never echo request headers
- preserve backend error messages when safe

## JSON mode

JSON output should:

- preserve backend response shape where possible
- wrap top-level lists consistently
- use structured error shape
- never include human screen decorations
- remain the stable scripting contract

## Backend gaps

Unsupported planned commands should always render:

```text
not_supported_by_backend: `COMMAND` needs a backend route first.
```

Do not fake success locally.
