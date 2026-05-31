# Phase 4 Prompt — Make LightRAG Metadata Non-Authoritative

Implement Phase 4 only.

Goal:

```text
Stop treating documents.metadata.lightrag.status as the source of truth.
```

Tasks:

```text
1. Search all metadata.lightrag.status reads/writes.
2. Replace authoritative reads with document.status + operation.status/stage.
3. Rename stored remote echo to last_remote_status if needed.
4. Keep remote IDs/fingerprints/last_remote_check_at in metadata.
5. Ensure processing-status maps remote status through backend logic.
6. Add regression tests.
```

Do not delete useful metadata like domain_id, remote document ID, or embedding fingerprint.
