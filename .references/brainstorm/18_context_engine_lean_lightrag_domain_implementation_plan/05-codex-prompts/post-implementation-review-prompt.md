# Post-Implementation Review Prompt

```text
Review the implemented LightRAG lifecycle simplification.

Confirm:
- UI exposes Create / Start / Stop / Delete only.
- No repair/recreate/regenerate/purge UI remains.
- Create does not auto-start.
- Start is the only boot/recovery path.
- Retrieval defaults are not in UI/API create payload.
- Retrieval defaults are written to domain.env from backend settings.
- Delete is safe archive/remove and preserves local documents.
- Provider secrets are not exposed in manifest/API/logs.
- Removed routes are absent or intentionally 410.
- Tests cover the new lifecycle.

Report any remaining entropy or accidental duplicate behavior.
```
