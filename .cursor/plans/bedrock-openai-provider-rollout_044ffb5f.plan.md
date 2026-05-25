---
name: bedrock-openai-provider-rollout
overview: Implement the full Bedrock OpenAI-compatible provider contract end-to-end, following TDD tracer-bullet slices and extending coverage through service/API secret-boundary checks.
todos:
  - id: tdd-slice-1-settings
    content: Write failing settings tests, then add provider fields in config + deploy settings mapping.
    status: completed
  - id: tdd-slice-2-domain-env
    content: Write failing domain.env rendering tests, then implement provider env append helpers in compose rendering.
    status: completed
  - id: tdd-slice-3-secret-boundary
    content: Add manifest/compose/service/API non-leak tests and patch only any exposed leak paths.
    status: completed
  - id: tdd-slice-4-env-docs
    content: Update .env.example provider section and key semantics; keep compatibility defaults.
    status: completed
  - id: verify-targeted-and-safety
    content: Run targeted and lightrag-focused test commands and confirm expected artifact behavior.
    status: completed
isProject: false
---

# Bedrock OpenAI-Compatible Provider Implementation Plan

## Scope Locked
- Implement the **full provider env contract** from [docs/brainstorm/06_context_engine_bedrock_openai_pkg/02_env_contract.md](docs/brainstorm/06_context_engine_bedrock_openai_pkg/02_env_contract.md).
- Update both required test files and also extend service/API tests for secret non-leak boundaries.

## TDD Vertical Slices (Red -> Green -> Refactor)

### Slice 1: Settings contract (parse and map)
- Start with failing tests in [tests/test_lightrag_deploy_settings.py](tests/test_lightrag_deploy_settings.py):
  - `.env.example` declares all provider keys.
  - `Settings` parses provider keys.
  - `LightRAGDeploySettings.from_app_settings()` maps all provider keys.
- Implement minimal code in:
  - [app/core/config.py](app/core/config.py) (add `lightrag_llm_*`, `lightrag_embedding_*`, `lightrag_openai_llm_*` fields).
  - [app/lightrag_deploy/settings.py](app/lightrag_deploy/settings.py) (add provider dataclass fields and mapping).

### Slice 2: domain.env rendering contract
- Add failing tests in [tests/test_lightrag_deploy_manifest_compose.py](tests/test_lightrag_deploy_manifest_compose.py):
  - Provider env block appears in generated `domain.env`.
  - Blank optional provider values are omitted.
  - Boolean provider flags render as lowercase `true`/`false`.
- Implement minimal rendering changes in [app/lightrag_deploy/compose.py](app/lightrag_deploy/compose.py):
  - Add env append helper with skip-empty behavior.
  - Append provider sections after existing storage/runtime settings.

### Slice 3: Secrets boundary hardening tests
- Add failing tests proving provider secrets stay only in `domain.env` and do not leak to manifest/compose/API responses:
  - [tests/test_lightrag_deploy_manifest_compose.py](tests/test_lightrag_deploy_manifest_compose.py)
  - [tests/test_lightrag_deploy_service.py](tests/test_lightrag_deploy_service.py)
  - [tests/test_api.py](tests/test_api.py) for admin/user response non-leak checks.
- Adjust implementation only if tests expose leaks (avoid widening manifest/domain models with provider secrets).

### Slice 4: Operator docs and defaults
- Update [/.env.example](.env.example) with full provider section and explicit Bedrock key semantics (`LIGHTRAG_API_KEY` vs `LIGHTRAG_LLM_BINDING_API_KEY`).
- Keep backward compatibility by preserving permissive settings parsing (`extra="ignore"` behavior remains unchanged).

## Verification
- Run targeted tests first:
  - `pytest tests/test_lightrag_deploy_settings.py tests/test_lightrag_deploy_manifest_compose.py`
- Then run expanded safety checks:
  - `pytest tests/test_lightrag_deploy_service.py tests/test_api.py -k lightrag`
- Validate generated `domain.env` includes provider config and secrets do not appear in generated compose/manifest artifacts.

## Risks to Watch
- Avoid confusing server auth (`LIGHTRAG_API_KEY`) with model-provider auth (`LIGHTRAG_LLM_BINDING_API_KEY`).
- Do not store provider keys in domain manifest models.
- Ensure bool serialization consistency in env output to prevent LightRAG parsing issues.