# Phase 2 Prompt — Add Operation Fields to Jobs

Implement Phase 2 only.

Goal:

```text
Make jobs operation-compatible while avoiding a risky table rename.
```

Add missing columns:

```text
resource_type
resource_id
stage
message
progress_current
progress_total
started_at
finished_at
```

If earlier refactors already added some fields, add only missing fields.

Tasks:

```text
1. Add Alembic migration.
2. Update SQLAlchemy row.
3. Backfill document jobs.
4. Add repository update methods for stage/message/progress.
5. Make upload response return operation_id/job_id and status_url.
6. Add tests.
```

Do not rename jobs table in this phase.
