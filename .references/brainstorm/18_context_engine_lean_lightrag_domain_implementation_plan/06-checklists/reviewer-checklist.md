# Reviewer Checklist

Use this when reviewing the PR.

## Product surface

- [ ] No extra lifecycle verbs appear in UI.
- [ ] Delete copy clearly says local document records are preserved.
- [ ] Provider changes say restart is required.

## API surface

- [ ] Removed endpoints are not in OpenAPI or are intentionally 410.
- [ ] Create schema is small.
- [ ] Retrieval defaults are not accepted from frontend.

## Backend internals

- [ ] Start is idempotent enough to refresh stale env/compose.
- [ ] Secrets are not logged or returned.
- [ ] Domain embedding snapshot is preserved.
- [ ] Postgres provisioning remains covered.

## Tests

- [ ] Create no-start test exists.
- [ ] Start env refresh test exists.
- [ ] Delete preservation test exists.
- [ ] Removed UI actions are tested absent.
