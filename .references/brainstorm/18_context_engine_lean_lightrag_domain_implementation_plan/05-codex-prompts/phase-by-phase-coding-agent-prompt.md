# Phase-by-Phase Coding Agent Prompt

```text
Implement the lean LightRAG lifecycle refactor one phase at a time.

Do not proceed to the next phase until tests/checks for the current phase pass.

Phase 1:
- Remove repair/recreate/regenerate/purge UI actions.
- Remove retrieval defaults from CreateDomainForm.
- Remove start:true from create payload.

Phase 2:
- Remove frontend API client methods for removed operations.
- Remove backend routes for repair/recreate/regenerate/purge-preview/purge.
- Remove create request fields: start and retrieval defaults.

Phase 3:
- Consolidate LightRAGDomainService so up/start is the only boot path.
- Move artifact regeneration into private helpers used by up.
- Do not expose repair/recreate/regenerate.

Phase 4:
- Source retrieval defaults from backend/deployment settings.
- Write retrieval defaults into domain.env.
- Stop reading retrieval defaults from UI/API.

Phase 5:
- Add LightRAGRuntimeConfigResolver if it reduces wiring spread.
- Keep secrets out of manifest/API/logs.

Phase 6:
- Update tests and docs.

For each phase, output:
- files changed;
- behavior changed;
- tests added/updated;
- risks;
- next phase.
```
