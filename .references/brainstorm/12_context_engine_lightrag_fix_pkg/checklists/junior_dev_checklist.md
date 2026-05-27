# Junior Developer Checklist

## Before coding

- [ ] Pull latest `main`.
- [ ] Start stack locally.
- [ ] Create or identify `fatigue` LightRAG domain.
- [ ] Confirm current upload failure.
- [ ] Run DNS checks from `api` and `worker` containers.
- [ ] Capture current domain manifest entry for `fatigue`.

## During coding

### Runtime resolver

- [ ] Find where `LightRAGDomainRuntime.base_url` is set.
- [ ] Change it to compute runtime URL.
- [ ] Do not remove legacy `base_url` support until migration is planned.
- [ ] Add unit tests for socket/host/legacy modes.

### Compose

- [ ] Find generated LightRAG Compose code.
- [ ] Add/confirm external network.
- [ ] Add/confirm service alias.
- [ ] Add test for generated YAML.

### Health probe

- [ ] Add `app/services/lightrag_domain_health.py`.
- [ ] Return structured health result.
- [ ] Test DNS failure.
- [ ] Test HTTP failure.
- [ ] Test success.

### Repair endpoint

- [ ] Add admin endpoint.
- [ ] Regenerate domain before start/recreate.
- [ ] Run health probe after Docker operation.
- [ ] Persist accurate status.
- [ ] Return diagnostics.

### Upload guardrail

- [ ] Add pre-upload reachability check.
- [ ] Do not enqueue ingestion job if domain unreachable.
- [ ] Make error actionable.
- [ ] Ensure no API keys/secrets leak in error response.

## Before PR

- [ ] Run `pytest`.
- [ ] Run targeted LightRAG tests.
- [ ] Run grep check for duplicate URL logic.
- [ ] Manually repair `fatigue`.
- [ ] Confirm API can resolve `lightrag_fatigue`.
- [ ] Confirm worker can resolve `lightrag_fatigue`.
- [ ] Upload test document.
- [ ] Query/retrieve evidence.
- [ ] Test graph endpoint/UI.

## Reviewer questions to answer in PR description

1. Where is the single source of truth for runtime LightRAG URL selection?
2. How does the system detect DNS failure differently from HTTP timeout?
3. What happens if Docker Compose returns success but LightRAG is not reachable?
4. How does an admin repair a broken domain?
5. How does the upload path avoid enqueueing doomed ingestion jobs?
