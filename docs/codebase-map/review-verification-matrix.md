# Review Verification Matrix

Source review: `.references/brainstorm/08_context_engine_codebase_review/context_engine_codebase_review_combined.md`

This matrix verifies key recommendations against the current codebase and records implementation actions in this hardening pass.

| Recommendation | Current Code Status | Action In This Pass |
|---|---|---|
| Remove default reliance on external `LIGHTRAG_IMAGE` and rely on internal LightRAG package build path | `Settings.lightrag_image` defaults to `ghcr.io/hkuds/lightrag:latest`; build path exists but is optional (`lightrag_dockerfile` / `lightrag_build_context`) | Remove `lightrag_image` from active settings contract and set default deploy behavior to local build (`docker/lightrag.Dockerfile`, `.`) |
| Validate production/runtime config more strictly | `validate_runtime_settings` already checks DB backend, weak `SECRET_KEY`, wildcard origins, weak seed password in production | Keep existing checks and add remaining policy checks relevant after image removal |
| Keep canonical `/retrieve` and stable response contract | `/retrieve` exists; contract tests exist but coverage of failure modes and evidence-field stability is limited | Add/adjust integration tests for failure semantics and evidence contract fields |
| LightRAG failure semantics should be explicit | LightRAG remote usage is mandatory; not all timeout/unavailable branches are locked by focused tests | Add test coverage for timeout/unavailable behavior through public interfaces |
| Resolve TUI/CLI policy contradictions | `AGENTS.md` says CLI unsupported; `README.md` and some docs still present terminal UI as supported | Align docs only (no CLI code/test deletion in this pass) |
| Update deployment env examples to match active contract | `.env.lightrag-deploy.example` still includes `LIGHTRAG_IMAGE` and empty build knobs | Update examples to build-first defaults and remove image-driven defaults |

## Verified Code Locations

- `app/core/config.py`
- `app/lightrag_deploy/settings.py`
- `app/lightrag_deploy/compose.py`
- `.env.lightrag-deploy.example`
- `README.md`
- `AGENTS.md`
- `tests/test_lightrag_deploy_settings.py`
- `tests/test_lightrag_deploy_manifest_compose.py`
