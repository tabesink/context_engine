# Phase Inspection Checklists

## Global checklist for every phase

- [ ] Phase scope was not exceeded.
- [ ] No direct frontend call to LightRAG was introduced.
- [ ] Existing auth/admin boundaries remain intact.
- [ ] No duplicate API client was created when an existing one could be extended.
- [ ] No broad visual redesign was mixed into functional work.
- [ ] UI follows flat grayscale, compact card, no-shadow rules.
- [ ] Tests/build/lint were run or pre-existing failures were documented.
- [ ] Phase report was provided.

## Phase 0 checklist

- [ ] UI surface map produced.
- [ ] API client map produced.
- [ ] State store map produced.
- [ ] Proposed primitives are minimal.
- [ ] No feature UI was implemented prematurely.

## Phase 1 checklist

- [ ] Settings shell has stable left navigation.
- [ ] Existing Account route remains functional.
- [ ] Admin-only entries are gated.
- [ ] Placeholder routes do not fake data.
- [ ] Visual density is acceptable.

## Phase 2 checklist

- [ ] Normalized backend schemas exist.
- [ ] LightRAG is backend-only.
- [ ] Raw LightRAG payloads are not frontend contracts.
- [ ] User-safe and admin detailed routes are separated.
- [ ] Stale/failure behavior is defined.
- [ ] Backend tests cover mapping/auth/failure behavior.

## Phase 3 checklist

- [ ] Admin domain lifecycle UI is implemented.
- [ ] Visible lifecycle actions are simplified.
- [ ] Recreate/regenerate are hidden or clarified.
- [ ] Danger Zone handles archive/purge safely.
- [ ] Domain status polling is deduplicated.

## Phase 4 checklist

- [ ] Document status table/cards implemented.
- [ ] Status/stage labels are understandable.
- [ ] Failures are actionable.
- [ ] Retry action is shown only if supported.
- [ ] Polling only runs while relevant UI is visible.

## Phase 5 checklist

- [ ] Job queue route is admin-only.
- [ ] Job statuses align with document/domain statuses.
- [ ] Event tail is useful and compact.
- [ ] No full observability platform was created.

## Phase 6 checklist

- [ ] Regular user sees only safe status.
- [ ] Indicator is subtle and not noisy.
- [ ] Chat retrieval is not blocked unless backend requires it.
- [ ] Source clicks do not mutate retrieval filters.
- [ ] No admin-only messages leak.

## Phase 7 checklist

- [ ] Duplicate status chips/cards consolidated.
- [ ] Duplicate polling removed.
- [ ] Duplicate API clients removed or documented.
- [ ] Full backend/frontend validation completed.
- [ ] Remaining debt documented.
