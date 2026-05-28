# Phase 7 — Final Hardening and Cleanup

## Goal

Consolidate duplicated UI/status code, verify contracts, and document remaining technical debt after all surfaces are implemented.

## Scope

Allowed:

- Remove duplicate status chips/cards.
- Consolidate polling helpers.
- Consolidate API clients.
- Rename ambiguous components.
- Add missing tests.
- Improve docs.
- Remove unused imports/dead code.

Not allowed:

- Major redesign.
- Deleting public backend routes without deprecation plan.
- Changing lifecycle semantics.
- Adding new status systems.

## Audit commands

```bash
rg -n "StatusChip|DocumentStatusChip|JobStatusChip|Domain.*Status|ProcessingStatus" client/src
rg -n "setInterval|poll|Polling|use.*Status" client/src
rg -n "apiRequest|fetch\(|/processing-status|/jobs|/documents|/lightrag" client/src
rg -n "pipeline_status|track_status|status_counts|processing-status|ingestion-status" app tests
rg -n "TODO|deprecated|legacy|duplicate|FIXME" app client tests docs
```

## Consolidation targets

- One frontend processing-status API client.
- One frontend polling hook/store.
- One shared status chip primitive.
- One shared empty/loading/error panel primitive.
- No raw LightRAG frontend parsing.
- No duplicate domain status cards.
- No duplicated destructive confirmation dialogs.

## Full validation

```bash
python -m pytest -q
cd client
npm run lint
npm run build
```

If the repo has typecheck/test scripts:

```bash
cd client
npm run typecheck
npm test
```

## Final report

Produce:

```md
# Context Engine Surface UI Final Report

## Summary
## Files changed
## APIs added/changed
## UI surfaces added
## State/polling architecture
## Auth boundaries verified
## Redundancy removed
## Tests run
## Remaining technical debt
## Recommended next work
```

## Human inspection gate

Inspect complete flow:

1. Admin opens Settings → LightRAG Domains.
2. Admin sees domain lifecycle status.
3. Admin can start/stop/repair/archive safely.
4. Admin can inspect document processing status.
5. Admin can inspect jobs/events.
6. Regular user sees only safe indexing status.
7. Chat retrieval still works.
8. Source Navigator still works.
9. Frontend never calls LightRAG directly.
