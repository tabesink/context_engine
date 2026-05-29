# Coding Agent Review Checklist

Use this to review generated code before accepting it.

## Architecture review

```text
[ ] Does the change reduce state duplication?
[ ] Does every status/state field have one owner?
[ ] Are route handlers thin?
[ ] Are status transitions centralized in services/helpers?
[ ] Are migrations expand-migrate-contract rather than destructive first?
```

## Migration review

```text
[ ] Migration has a clear upgrade path.
[ ] Data backfill is included.
[ ] Nullable columns are used during transition.
[ ] FK is only added after invalid references are handled.
[ ] Downgrade either works or explicitly states it is not supported.
```

## Test review

```text
[ ] Tests cover document operations.
[ ] Tests cover domain operations.
[ ] Tests cover failure state.
[ ] Tests cover old API compatibility if old API remains.
[ ] Tests cover document navigation response shape.
```

## UI/API review

```text
[ ] UI action vocabulary is Create / Start / Stop / Delete.
[ ] Domain card More menu does not include Upload Documents.
[ ] Domain card More menu does not include View Documents.
[ ] Domain card More menu does not include View Logs.
[ ] Removed lifecycle actions are not first-class UI verbs.
```
