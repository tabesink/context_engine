# Context Engine Lean LightRAG Domain Implementation Plan

This package is a junior-developer and coding-agent handoff for simplifying the Context Engine LightRAG Docker domain lifecycle.

## Final product target

Expose only these domain lifecycle actions:

```text
Create
Start
Stop
Delete
```

Remove from the product/API surface:

```text
repair
recreate
regenerate
purge-preview
purge
```

Remove runtime retrieval defaults from UI/API/domain runtime editing:

```text
top_k
chunk_top_k
chunk_rerank_top_k
max_token_for_text_unit
max_token_for_global_context
max_token_for_local_context
precise / balanced / broad / custom retrieval profiles
```

Retrieval defaults become backend/deployment configuration written into `domain.env` during domain artifact generation.

## Main architecture principle

```text
Public product model: Create / Start / Stop / Delete
Internal implementation: prepare files / write env / write compose / provision Postgres / start Docker / health check
```

Admins can still change provider API keys and model profiles at runtime through AI Settings. Running LightRAG containers do not automatically receive changed Docker env vars. The app should communicate that a restart is required, and Start should refresh `domain.env` before booting.

## Package contents

```text
00-overview/
  executive-summary.md
  final-target-model.md
  junior-dev-mental-model.md

01-architecture/
  lean-ascii-diagrams.md
  provider-model-wiring.md
  retrieval-defaults-policy.md
  target-api-surface.md
  target-service-boundaries.md

02-implementation-phases/
  phase-0-impact-scan.md
  phase-1-frontend-ui-simplification.md
  phase-2-api-contract-cleanup.md
  phase-3-service-consolidation.md
  phase-4-retrieval-defaults-removal.md
  phase-5-runtime-config-resolver.md
  phase-6-tests-docs-cleanup.md

03-patch-guides/
  frontend-patch-guide.md
  backend-route-patch-guide.md
  backend-service-patch-guide.md
  settings-and-env-patch-guide.md
  data-retention-delete-policy.md

04-tests/
  backend-test-plan.md
  frontend-test-plan.md
  integration-smoke-test.md
  regression-matrix.md

05-codex-prompts/
  master-implementation-prompt.md
  phase-by-phase-coding-agent-prompt.md
  impact-review-prompt.md
  post-implementation-review-prompt.md

06-checklists/
  pre-edit-checklist.md
  definition-of-done.md
  reviewer-checklist.md

07-reference/
  files-to-edit.md
  removed-surface-map.md
  final-endpoint-map.md
  glossary.md
```

## Recommended execution order

1. Run the impact scan.
2. Simplify frontend first so the product surface becomes small.
3. Clean backend routes and API contracts.
4. Consolidate service internals so Start is the only boot path.
5. Remove retrieval defaults from UI/API/manifest request flow and source them from backend env settings.
6. Add tests.
7. Update docs.

Do not combine all work into one giant PR unless this is a small private prototype. For safer review, use one PR per phase.
