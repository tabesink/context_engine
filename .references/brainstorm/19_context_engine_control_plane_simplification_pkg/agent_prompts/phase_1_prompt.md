# Phase 1 Coding Agent Prompt

Implement Phase 1 only: make `jobs` operation-compatible without breaking existing job behavior.

Tasks:

1. Add Alembic migration with columns:
   - `resource_type`
   - `resource_id`
   - `requested_by_user_id`
   - `progress_current`
   - `progress_total`
   - `started_at`
   - `finished_at`

2. Backfill existing rows:
   - document jobs become `resource_type=document`, `resource_id=document_id`
   - other jobs become `resource_type=system`

3. Update ORM in `app/storage/tables.py`.

4. Add operation domain model or compatibility alias in `app/domain/models.py`.

5. Add repository/service methods for operations.

6. Update document ingestion to create operations with `resource_type=document`.

7. Update domain lifecycle actions to create operations with `resource_type=domain`.

8. Keep old job endpoints working or alias them.

9. Add tests for create/list/status transitions.

Do not rename `jobs` table in this phase.
Do not modify document structure arrays in this phase.
Do not rename LightRAG lifecycle table in this phase.
