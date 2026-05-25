# Junior Developer Checklist

## Before Editing

- [ ] Pull latest `context_engine`.
- [ ] Run existing tests: `python -m pytest -q`.
- [ ] Find current route registration in `app/main.py`.
- [ ] Confirm current retrieval route in `app/api/routes/retrieve.py`.
- [ ] Confirm current schemas in `app/schemas/retrieval.py`.
- [ ] Confirm retrieval service method: `RetrievalService.retrieve(...)`.

## Backend Implementation Baseline

- [ ] Confirm `POST /retrieve` route exists.
- [ ] Route uses existing `get_current_user` auth dependency.
- [ ] Route uses existing `get_session` DB dependency.
- [ ] Route accepts `RetrieveRequest`.
- [ ] Route returns `RetrieveResponse`.
- [ ] Route calls `RetrievalService(session).retrieve(...)`.
- [ ] Keep `/query/retrieve` removed unless a separate API decision restores it.
- [ ] Do not duplicate retrieval logic.
- [ ] Do not call LightRAG directly from route.
- [ ] Do not add new database tables.

## Evidence Schema

- [ ] Confirm evidence cards have `evidence_id`, `document_id`, `source_engine`, `text`, `score`, page fields, section title, and metadata.
- [ ] Confirm `source_path`, `document_title`, `chunk_id`, and `reference_id` are projected when metadata provides them.
- [ ] Update `evidence_mapper.py` if new display fields are added later.
- [ ] Keep `metadata` for raw optional details.

## Assets

- [ ] Confirm `include_assets` works.
- [ ] Confirm `include_thumbnails` works.
- [ ] Confirm `max_assets` is respected.
- [ ] Do not return assets unless requested.

## Error Handling

- [ ] Empty evidence returns 200 with `evidence: []`.
- [ ] Auth failure returns existing auth failure behavior.
- [ ] Domain/document mismatch returns 400.
- [ ] LightRAG invalid response maps to 502.
- [ ] LightRAG unavailable maps to 503.

## WebUI

- [ ] Add right-side panel component.
- [ ] Add loading state.
- [ ] Add success state.
- [ ] Add empty state.
- [ ] Add error state.
- [ ] Render source engine badge.
- [ ] Render document/source label.
- [ ] Render section and page range.
- [ ] Render snippet.
- [ ] Render asset thumbnails if present.
- [ ] Keep backend evidence order.

## Tests

- [ ] Add backend test for `/retrieve` auth.
- [ ] Add backend test for `/retrieve` evidence shape.
- [ ] Keep or update removed-route test for `/query/retrieve` returning 404.
- [ ] Add debug admin-only test.
- [ ] Add domain/document mismatch test.
- [ ] Add WebUI tests for loading/success/empty/error.
- [ ] Run full test suite.

## TDD Discipline

- [ ] Add one public behavior test first.
- [ ] Make the smallest implementation change to pass that test.
- [ ] Repeat in vertical slices instead of writing all tests first.
- [ ] Refactor only after the current slice is green.

## PR Review

- [ ] PR title clearly says evidence side panel support.
- [ ] PR does not mention unrelated refactors.
- [ ] PR does not include `easy-deploy-lightrag` backend code.
- [ ] PR does not add duplicate auth routes.
- [ ] PR does not add a second retrieval service.
- [ ] Screenshots or response examples are included.
