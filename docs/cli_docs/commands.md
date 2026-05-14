# Command Reference

All commands accept `--api-base-url` at the root and `--output human|json` at the command level.

```bash
ragcli --api-base-url http://127.0.0.1:8000 COMMAND
```

## Session Commands

```bash
ragcli login --email admin@example.com
ragcli logout
ragcli auth me
```

`login` prompts for `--password` if it is not provided. The password is sent to `/auth/login` and is never stored.

## Document Commands

```bash
ragcli documents list
ragcli documents show --document-id DOC_ID
ragcli documents structure --document-id DOC_ID
ragcli documents page --document-id DOC_ID --page-number 1
ragcli documents retrieve --query "payment terms"
ragcli documents retrieve --query "reset procedure" --mode hybrid --top-k 3
ragcli documents answer --query "what does the manual say about reset?"
ragcli query --query "what does the manual say about reset?"
```

Supported retrieval modes are the backend modes: `auto`, `semantic`, `navigation`, and `hybrid`.

## Admin Document Commands

```bash
ragcli admin documents upload --file ./manual.pdf
ragcli admin documents list
ragcli admin documents index --document-id DOC_ID
ragcli admin documents reindex --document-id DOC_ID
ragcli admin documents delete --document-id DOC_ID
```

Admin commands require a token for an admin user. Normal users should receive the backend `403` response rendered consistently in human and JSON modes.

## Job Commands

```bash
ragcli jobs list
ragcli jobs status --job-id JOB_ID
ragcli jobs retry --job-id JOB_ID
```

Jobs describe indexing work. Upload responses include a `job_id`; use `jobs status` to inspect it.

## Planned Commands

The full target CLI also reserves this surface:

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

These commands should remain explicit backend gaps until corresponding FastAPI routes and behavior tests exist.

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
ragcli documents retrieve --query "installation steps" --output json
```

```json
{
  "mode": "navigation",
  "evidence": []
}
```
