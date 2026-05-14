# Command Reference

Root options are accepted before the command group:

```bash
ragcli --api-base-url http://127.0.0.1:8000 --config-dir ~/.context-engine/ragcli COMMAND
```

Most commands accept `--output human|json`. JSON is the stable scripting contract.

## Session Commands

```bash
ragcli login --email admin@example.com
ragcli logout
ragcli auth me
```

`login` prompts for `--password` if it is not provided. The password is sent to `/auth/login` and is never stored. The saved session includes the backend base URL and access token; protected commands use that saved base URL.

## Document Commands

```bash
ragcli documents list
ragcli documents show --document-id DOC_ID
ragcli documents structure --document-id DOC_ID
ragcli documents page --document-id DOC_ID --page-number 1
ragcli documents retrieve --query "payment terms"
ragcli documents retrieve --query "reset procedure" --mode hybrid --top-k 3
ragcli documents retrieve --query "reset procedure" --document-id DOC_ID
ragcli documents retrieve --query "reset procedure" --document-id DOC1 --document-id DOC2
ragcli documents answer --query "what does the manual say about reset?"
ragcli documents answer --query "what does the manual say about reset?" --document-id DOC_ID
ragcli query --query "what does the manual say about reset?"
ragcli query --query "what does the manual say about reset?" --document-id DOC_ID
```

Supported retrieval modes are `auto`, `semantic`, `navigation`, and `hybrid`. Repeat `--document-id` to send a `document_ids` array. Query commands include `include_debug` and `allow_general_fallback` in the request body; the backend only returns debug details to admins.

## LightRAG Commands

```bash
ragcli lightrag graphs show --label LABEL
ragcli lightrag graphs show --label LABEL --max-depth 2 --max-nodes 100
ragcli lightrag labels list
ragcli lightrag labels popular --limit 20
ragcli lightrag labels search --query "install" --limit 20
```

LightRAG commands call backend graph proxy routes:

- `GET /graphs`
- `GET /graph/label/list`
- `GET /graph/label/popular`
- `GET /graph/label/search`

The CLI does not connect to LightRAG directly. If the backend has `LIGHTRAG_ENABLED=false`, these commands render the backend's disabled-service error.

## Admin Document Commands

```bash
ragcli admin documents upload --file ./manual.pdf
ragcli admin documents list
ragcli admin documents index --document-id DOC_ID
ragcli admin documents reindex --document-id DOC_ID
ragcli admin documents delete --document-id DOC_ID
ragcli admin audit-logs list
ragcli admin query-logs list
```

Admin commands require a token for an admin user. Normal users receive the backend `403` response rendered through the same error path as other API failures.

When `LIGHTRAG_ENABLED=false`, upload responses include a local indexing `job_id`. When LightRAG is enabled, upload forwards to the remote service and may return `job_id: null` with `lightrag.*` metadata.

## Job Commands

```bash
ragcli jobs list
ragcli jobs status --job-id JOB_ID
ragcli jobs retry --job-id JOB_ID
```

Jobs describe local indexing work. Use `jobs status` to inspect upload/index/reindex jobs created by the local path.

## Planned Commands

The CLI reserves this surface but the current backend has no matching routes:

```bash
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
ragcli runs status
ragcli runs cancel
ragcli runs approvals list
ragcli runs approvals approve
ragcli runs approvals reject
ragcli admin corpus publish
ragcli admin corpus rollback
ragcli admin corpus cleanup
```

These commands return `not_supported_by_backend` until corresponding FastAPI routes and behavior tests exist.

## JSON Examples

```bash
ragcli documents list --output json
```

```json
{
  "documents": [
    {
      "id": "doc_123",
      "filename": "manual.pdf",
      "status": "ready"
    }
  ]
}
```

```bash
ragcli documents retrieve --query "installation steps" --include-debug --output json
```

```json
{
  "query": "installation steps",
  "mode": "navigation",
  "evidence": [
    {
      "evidence_id": "nav-1",
      "document_id": "doc_123",
      "source_engine": "navigation",
      "text": "Installation steps...",
      "score": 0.8,
      "page_start": 1,
      "page_end": 1,
      "section_title": "Installation",
      "metadata": {}
    }
  ],
  "debug": {
    "requested_mode": "auto",
    "selected_engine": "navigation"
  }
}
```

For non-admin users, `debug` is omitted even when `--include-debug` is sent.
