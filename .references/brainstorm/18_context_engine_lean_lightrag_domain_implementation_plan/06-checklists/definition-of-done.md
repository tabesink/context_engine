# Definition of Done

- [ ] Lifecycle UI shows only Create, Start, Stop, Delete.
- [ ] Create form has no retrieval defaults.
- [ ] Create payload has no `start` and no retrieval defaults.
- [ ] Backend create route does not call repair/start.
- [ ] Removed routes are gone or return intentional `410 Gone`.
- [ ] Start/up handles runtime artifact refresh.
- [ ] Start/up writes `domain.env` with provider config and retrieval defaults from backend config.
- [ ] Delete is safe archive/remove and preserves local document data.
- [ ] Purge service/models/config removed if unused.
- [ ] Provider key change communicates restart required.
- [ ] Tests pass.
- [ ] Docs updated.
