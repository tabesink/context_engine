# Integration Smoke Test

Run manually after implementation.

## Steps

1. Start stack.
2. Login as admin.
3. Open Settings / AI Settings.
4. Configure provider key and model profiles.
5. Open Settings / LightRAG Domains.
6. Confirm Create form has no retrieval defaults.
7. Create domain.
8. Confirm domain appears as configured/stopped.
9. Confirm it did not auto-start.
10. Click Start.
11. Confirm `domain.env` was written with provider secrets and retrieval defaults from backend config.
12. Confirm container starts and health status updates.
13. Click Stop.
14. Confirm container stops.
15. Click Delete.
16. Confirm domain disappears from active domain list.
17. Confirm documents/local rows are preserved if any existed.
18. Try removed routes manually; confirm 404 or 410.

## Removed route curl checks

```bash
curl -X POST "$API/admin/lightrag/domains/test/repair" -H "Authorization: Bearer $TOKEN"
curl -X POST "$API/admin/lightrag/domains/test/recreate" -H "Authorization: Bearer $TOKEN"
curl -X POST "$API/admin/lightrag/domains/test/regenerate" -H "Authorization: Bearer $TOKEN"
curl -X POST "$API/admin/lightrag/domains/test/purge-preview" -H "Authorization: Bearer $TOKEN"
curl -X DELETE "$API/admin/lightrag/domains/test/purge?confirm_domain_id=test" -H "Authorization: Bearer $TOKEN"
```
