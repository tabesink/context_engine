Here is the continuation you can append after the previous prompt.

---

## 10. Detailed Coding Agent Instructions

After producing the plan, implement the CLI integration incrementally.

Do **not** rewrite the entire CLI at once. Work in small, reviewable changes.

For each phase:

1. Inspect the existing files.
2. Identify what can be reused.
3. Make the smallest reasonable code change.
4. Add or update tests.
5. Run the relevant checks.
6. Summarize what changed and why.

---

## 11. Existing Code to Preserve

Preserve and reuse these existing components unless there is a strong reason to change them:

### API Client

Reuse the current `ApiClient` abstraction because it already supports:

* JSON `GET` and `POST`
* Bearer token authorization
* File upload using multipart form data
* SSE streaming
* Typed API errors through `ApiClientError`

Reference: 

Do not replace this with `requests` or `httpx` unless the plan clearly justifies why.

---

### Chat Streaming

Reuse the existing `ApiChatLoop` pattern because it already handles:

* Human-readable streaming output
* JSON event output
* `message.delta`
* `message.completed`
* `run.started`
* `run.completed`
* `run.failed`
* `approval.required`
* Interactive approval handling

Reference: 

Extend this only where needed to support the Multi-User Hybrid RAG backend event schema.

---

### Credential Storage

Reuse the existing credential storage approach:

* Store only backend URL and access token
* Prefer OS keyring
* Fall back to a local credentials file
* Do not store passwords

Reference: 

Add clear warnings if fallback file storage is used.

---

### Typer CLI Structure

Preserve the Typer-based command structure where possible.

The current CLI already has command groups for:

* Users
* Agents
* Conversations
* Messages
* Documents
* Runs
* Approvals

Reference: 

Rename commands only if necessary to better match the Multi-User Hybrid RAG domain.

---

## 12. Suggested Target CLI Commands

Design the CLI around the following command groups:

```bash
ragcli login
ragcli logout

ragcli users create
ragcli users list

ragcli retrievers list
ragcli agents list

ragcli conversations create
ragcli conversations list
ragcli conversations show

ragcli chat

ragcli messages send
ragcli messages list

ragcli documents list
ragcli documents show
ragcli documents structure
ragcli documents content
ragcli documents search
ragcli documents retrieve

ragcli admin documents upload
ragcli admin corpus publish
ragcli admin corpus rollback
ragcli admin corpus cleanup

ragcli runs status
ragcli runs cancel
ragcli runs approvals list
ragcli runs approvals approve
ragcli runs approvals reject
```

Keep command names boring and obvious. Avoid clever naming.

---

## 13. Recommended Folder Structure

Refactor toward this structure only if it improves maintainability:

```text
cli/
  __init__.py

  app.py
  main.py

  api/
    __init__.py
    client.py
    errors.py
    schemas.py

  auth/
    __init__.py
    credentials.py
    session.py

  commands/
    __init__.py
    auth.py
    users.py
    agents.py
    conversations.py
    messages.py
    documents.py
    admin.py
    runs.py

  streaming/
    __init__.py
    chat_loop.py
    events.py
    renderer.py

  ui/
    __init__.py
    menu.py
    tables.py
    output.py

  config/
    __init__.py
    settings.py

tests/
  cli/
    test_api_client.py
    test_auth_commands.py
    test_chat_streaming.py
    test_documents_commands.py
    test_admin_permissions.py
```

Do not over-split the code if the CLI is still small. Use this structure as a direction, not as mandatory complexity.

---

## 14. Required API Route Contract

The backend should expose routes similar to the following.

### Auth

```http
POST /v1/auth/login
POST /v1/auth/logout
GET  /v1/auth/me
```

### Users

```http
POST /v1/users
GET  /v1/users
```

### Agents / Retrievers

```http
GET /v1/agents
GET /v1/retrievers
```

### Conversations

```http
POST /v1/conversations
GET  /v1/conversations
GET  /v1/conversations/{conversation_id}
```

### Messages

```http
POST /v1/conversations/{conversation_id}/messages
GET  /v1/conversations/{conversation_id}/messages
```

### Runs

```http
GET  /v1/runs/{run_id}
POST /v1/runs/{run_id}/cancel
GET  /v1/runs/{run_id}/stream
```

### Documents

```http
GET /v1/documents
GET /v1/documents/{document_id}
GET /v1/documents/{document_id}/structure
GET /v1/documents/{document_id}/content?pages=1-3
POST /v1/documents/search
POST /v1/documents/retrieve
```

### Admin Corpus Management

```http
POST /v1/admin/documents/upload
POST /v1/admin/corpus/versions/{corpus_version_id}/publish
POST /v1/admin/corpus/versions/{corpus_version_id}/rollback
POST /v1/admin/corpus/cleanup
```

### Approvals

```http
GET  /v1/runs/{run_id}/approvals
POST /v1/runs/{run_id}/approvals/{approval_id}/approve
POST /v1/runs/{run_id}/approvals/{approval_id}/reject
```

---

## 15. Retrieval-Specific CLI Features

Because this is a **Hybrid RAG Application**, add retrieval commands that expose both semantic search and document navigation.

Example commands:

```bash
ragcli documents search --query "payment terms"
ragcli documents retrieve --query "explain warranty coverage"
ragcli documents structure --document-id DOC_ID
ragcli documents content --document-id DOC_ID --pages "4-7"
```

The CLI should support both:

### Semantic Retrieval

Used when the user asks a meaning-based question:

```bash
ragcli documents retrieve --query "What does the manual say about resetting the device?"
```

### Document Navigation

Used when the user wants a specific document section, page, heading, or table:

```bash
ragcli documents content --document-id DOC_ID --pages "10-12"
```

### Hybrid Debug Mode

Add a debug option for developers/admins:

```bash
ragcli documents retrieve \
  --query "How do I reset the pump?" \
  --debug
```

Debug output should include:

* Selected retriever
* Retrieved chunks
* Source document IDs
* Page numbers
* Scores
* Reranking result
* Final context passed to the LLM

Do not expose debug retrieval data to users unless authorized.

---

## 16. Expected SSE Event Schema

The backend streaming endpoint should emit events compatible with the existing CLI chat loop.

Recommended events:

```text
run.started
retrieval.started
retrieval.completed
message.delta
message.completed
approval.required
run.completed
run.failed
run.cancelled
```

Example SSE payloads:

```json
{
  "event": "run.started",
  "run_id": "run_123",
  "conversation_id": "conv_123"
}
```

```json
{
  "event": "retrieval.completed",
  "run_id": "run_123",
  "sources": [
    {
      "document_id": "doc_1",
      "title": "Manual.pdf",
      "page": 12,
      "score": 0.87
    }
  ]
}
```

```json
{
  "event": "message.delta",
  "delta": "The reset procedure is..."
}
```

```json
{
  "event": "message.completed"
}
```

```json
{
  "event": "run.completed",
  "run_id": "run_123"
}
```

The CLI should ignore unknown events gracefully and print them in dim/debug format.

---

## 17. Output Mode Requirements

Every command should support:

```bash
--output human
--output json
```

Human mode is for interactive users.

JSON mode is for scripts, automation, tests, and future UI wrappers.

Examples:

```bash
ragcli documents list --output json
```

```json
{
  "documents": [
    {
      "id": "doc_123",
      "doc_name": "manual.pdf",
      "doc_type": "pdf"
    }
  ]
}
```

The coding agent must preserve JSON mode during refactors.

---

## 18. Testing Requirements

Add tests for the following:

### API Client

* Sends Bearer token correctly
* Handles JSON responses
* Handles HTTP error payloads
* Handles backend connection failure
* Handles file uploads
* Parses SSE events

### Auth

* Login stores credentials
* Logout clears credentials
* Commands fail gracefully without login
* Token mismatch warning appears when API base URL changes

### Chat

* Creates conversation when only `--agent-id` is provided
* Sends message to existing conversation
* Streams message deltas
* Handles `approval.required`
* Handles failed run events

### Documents

* Lists documents
* Shows document metadata
* Fetches structure
* Fetches selected pages
* Upload is admin-only
* Publish/rollback/cleanup are admin-only

### Security

* Normal users cannot upload or publish
* Tokens are not printed
* Passwords are not stored
* Error messages do not leak sensitive backend details

---

## 19. Developer Experience Requirements

Add or update a `README.md` with examples:

```bash
ragcli login --username admin
ragcli agents list
ragcli conversations create --agent-id default-rag
ragcli chat --agent-id default-rag
ragcli documents list
ragcli documents structure --document-id DOC_ID
ragcli documents content --document-id DOC_ID --pages "1-3"
ragcli admin documents upload --file ./manual.pdf
```

Also include:

* How to set API base URL
* How credentials are stored
* How to use JSON output
* How to run tests
* How to debug backend connection errors
* Admin vs normal user command differences

---

## 20. Final Coding Agent Instruction

Use the existing CLI as the starting point.

First produce the plan.

Then implement in this order:

1. Align names and route contracts.
2. Refactor only where needed.
3. Preserve working auth and streaming behavior.
4. Add retrieval/document navigation commands.
5. Add admin ingestion workflows.
6. Add tests.
7. Update README.

Avoid speculative features.
Favor simple, reliable CLI workflows over complex abstractions.
The result should feel like a thin, dependable command-line client for the Multi-User Hybrid RAG Application.
