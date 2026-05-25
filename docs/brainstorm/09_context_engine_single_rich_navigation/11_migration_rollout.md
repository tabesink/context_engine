# 11 — Migration and Rollout Strategy

## Recommended PR Sequence

## PR 1 — Add `document_pages`

Scope:

```text
- Add `DocumentPageRow`.
- Add migration.
- Update repository save/load.
- Add repository tests.
```

No public API behavior change yet.

---

## PR 2 — Remove TOC Refinement

Scope:

```text
- Remove `TocRefiner` from ingestion.
- Remove TOC report route/schema/table.
- Add tests proving ingestion is deterministic.
```

---

## PR 3 — Move Page and Structure APIs to Rich Only

Scope:

```text
- Page API reads `document_pages`.
- Structure API removes fallback to `navigation_indexes`.
- Structure response includes pages.
- Add API tests.
```

---

## PR 4 — Add `RichNavigationEngine`

Scope:

```text
- Implement deterministic structure search.
- Wire retrieval service.
- Update navigation and hybrid tests.
```

---

## PR 5 — Stop Writing Old Local Navigation

Scope:

```text
- Remove or disable old indexing writes.
- Update upload/indexing flows.
- Add tests proving new documents do not write old tables.
```

---

## PR 6 — Delete Old Navigation Layer

Scope:

```text
- Drop old tables.
- Delete old code.
- Update docs.
- Run full regression.
```

## Rollout Notes

Do not drop old tables until:

```text
[ ] Existing documents are backfilled or intentionally discarded.
[ ] APIs no longer use old tables.
[ ] Retrieval no longer uses old tables.
[ ] Tests prove old runtime paths are gone.
```

## Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| Existing docs only have old parsed pages | Page API may 404 | Backfill `document_pages` from `parsed_documents`. |
| Parser does not populate pages | Missing page API output | Add parser tests for PDF, TXT, MD. |
| Removing TOC refinement reduces section quality | Less refined hierarchy | Accept for lean design; rely on deterministic parser output. |
| Rich navigation duplicates results | Noisy evidence | Dedupe by chunk/page/section priority. |
| Dropping tables too early | Data loss | Backfill and verify before drop migration. |
