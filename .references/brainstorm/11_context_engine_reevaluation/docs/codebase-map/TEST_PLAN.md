# Test Plan

## Backend Tests

### AI Settings

- admin can get AI settings
- regular user cannot get AI settings
- admin can update default LLM profile
- admin can update default embedding profile
- regular user cannot update defaults
- admin can create profile
- admin can update profile
- admin can set provider secret
- secret response is masked
- raw secret is not returned
- raw secret is not logged
- Ollama profile does not require API key if configured as local

### Migrations

- fresh DB migration creates AI settings tables
- fresh DB migration creates or preserves document domain fields
- `/admin/ai-settings` works after migration
- rollback/downgrade posture documented

### LightRAG Domains

- admin can create domain with embedding profile
- domain stores embedding snapshot/fingerprint
- domain env generation uses embedding snapshot
- domain env generation can use DB-stored provider secret
- missing provider secret fails clearly
- regular user cannot create/start/stop/delete domain
- domain cannot silently change embedding model after ingestion

### Upload and Ingestion

- regular user cannot upload
- admin upload requires valid domain
- upload fails for unknown domain
- upload persists `lightrag_domain_id`
- upload creates job
- worker persists local structure
- worker sends chunks to correct LightRAG domain
- failed LightRAG ingest marks job failed
- retry/requeue behavior works where expected
- document stores embedding fingerprint used

### Retrieval

- unauthenticated user cannot retrieve
- authenticated regular user can retrieve
- retrieval uses selected domain
- invalid domain fails clearly
- document filter outside domain fails clearly
- evidence includes stable fields
- `include_assets=true` returns assets where available
- LightRAG unavailable returns clear error

### Workspace Tree

- regular user can fetch workspace tree
- tree is domain-scoped
- tree excludes non-ready/unauthorized docs as intended
- tree includes documents, sections, pages, chunks, assets
- tree handles empty domain gracefully

## Frontend Tests

### Settings

- Settings sidebar shows Provider
- Provider route is admin-only
- non-admin does not see Provider route
- API key input masks stored status
- raw key is not displayed after save
- default LLM/embedding selection loads from backend
- save/update states display errors clearly

### Chat Retrieval

- chat sends `/retrieve`
- selected domain is included
- evidence response populates context panel
- no evidence shows empty state
- backend error shows user-friendly message

### Workspace Tree

- tree fetches selected domain structure
- tree updates on domain change
- tree renders documents and sections
- evidence click can link/highlight matching source where implemented

## Manual Smoke Test Script

1. Start fresh DB.
2. Run migrations.
3. Start API and frontend.
4. Login as admin.
5. Open Settings → Provider.
6. Set provider secret.
7. Select default LLM and embedding.
8. Create LightRAG domain with embedding profile.
9. Upload document to domain.
10. Confirm job succeeds.
11. Login as regular user.
12. Select domain in chat retrieval settings.
13. Ask a question.
14. Confirm answer/evidence returns.
15. Confirm context panel shows evidence.
16. Confirm workspace tree shows domain documents.
