# Phase 6 — Tests and Docs Cleanup

## Goal

Lock in the new low-entropy lifecycle with tests and docs.

## Update docs to say

```text
Lifecycle: Create / Start / Stop / Delete
Create does not start.
Start is the only boot path.
Delete is safe archive/remove.
Retrieval defaults come from backend config/domain.env.
Provider changes require restart.
```

## Remove docs that mention product use of

```text
repair
recreate
regenerate
purge
purge-preview
advanced retrieval defaults in create UI
```

## Tests to update

- Remove route tests for removed routes.
- Add route-not-present or 410 tests if compatibility mode used.
- Replace repair tests with Start tests.
- Replace purge tests with Delete data-retention tests.
- Add env writer tests for retrieval defaults from config.
- Add frontend tests proving removed buttons are absent.

## Acceptance criteria

- Backend tests pass.
- Frontend lint/build pass.
- Docs and UI agree.
- Junior developer can explain lifecycle in four verbs.
