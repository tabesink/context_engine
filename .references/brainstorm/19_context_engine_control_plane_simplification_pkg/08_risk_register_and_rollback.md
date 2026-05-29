# Risk Register and Rollback Plan

## Risk 1 — Breaking existing jobs routes

Cause:

```text
Renaming jobs -> operations too early.
```

Mitigation:

```text
Add operation-compatible columns first.
Keep existing job endpoints as aliases for one phase.
Use OperationRow mapped to jobs table if needed.
```

Rollback:

```text
Revert service changes. New columns can remain unused safely.
```

## Risk 2 — Documents reference missing LightRAG domains

Cause:

```text
documents.lightrag_domain_id is currently a string with no FK.
```

Mitigation:

```text
Run invalid domain audit before adding FK.
Create missing domain rows or clear invalid references.
```

Rollback:

```text
Do not add FK until data is clean.
```

## Risk 3 — Document navigation response changes

Cause:

```text
Removing duplicate JSON arrays before replacing read builders.
```

Mitigation:

```text
First derive arrays from canonical relations but keep API shape.
Only drop columns after UI and API tests pass.
```

Rollback:

```text
Keep columns for one release. Re-enable writer if needed.
```

## Risk 4 — Too much refactor in one PR

Cause:

```text
Combining domain, jobs, document structure, and provider settings changes.
```

Mitigation:

```text
Use separate PRs. Do not rename ai_model_settings during domain/job refactor.
```

Rollback:

```text
Each phase must be independently revertible.
```

## Risk 5 — UI still exposes removed domain actions

Cause:

```text
Frontend menu not updated after backend simplification.
```

Mitigation:

```text
Search frontend for repair/recreate/regenerate/purge/view logs/upload documents/view documents.
Remove these from domain card More menu.
```

Rollback:

```text
No rollback needed if backend routes still exist internally. This is UI-only exposure cleanup.
```
