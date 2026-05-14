---
name: env-first-runtime-config
overview: Adopt `.env` as deployment config source with env-overrides-YAML behavior, auto-load `.env` in backend and CLI, and keep strict `llm.api_key_env` contract.
todos:
  - id: add-dotenv-bootstrap
    content: Add shared `.env` loader and call it from backend and CLI entrypoints
    status: completed
  - id: merge-env-over-yaml
    content: Implement environment-overrides-YAML behavior in config loading with strict validation
    status: completed
  - id: author-env-example
    content: Populate `.env.example` with backend core, runtime LLM, limits/timeouts, and feature toggles
    status: completed
  - id: update-docs-and-vars
    content: Document precedence and variable contract in deploy/config docs
    status: completed
  - id: add-precedence-tests
    content: Add tests covering env override behavior and strict llm.api_key_env failures
    status: completed
isProject: false
---

# Env-First Config Integration

## Goal
Use `.env`/environment variables as primary deployment config, with values overriding `config.user.yaml`, while preserving strict runtime LLM key semantics (`llm.api_key_env` required).

## Decisions Locked
- Env precedence: environment values override YAML.
- Auto-load scope: both backend and CLI entrypoints load `.env` automatically.
- LLM key contract: keep explicit `llm.api_key_env` required.
- `.env.example` scope: backend core, runtime LLM, limits/timeouts, feature toggles.

## Implementation Plan
- Add dotenv loading bootstrap (shared helper) and invoke from both backend and CLI startup paths:
  - [`d:\Projects\clawagent\src\backend\app.py`](d:\Projects\clawagent\src\backend\app.py)
  - [`d:\Projects\clawagent\src\cli\main.py`](d:\Projects\clawagent\src\cli\main.py)
  - New helper module under [`d:\Projects\clawagent\src\`](d:\Projects\clawagent\src\) for consistent `.env` resolution.
- Implement env-overrides-YAML merge behavior for runtime/app config:
  - [`d:\Projects\clawagent\src\agent\utils\config.py`](d:\Projects\clawagent\src\agent\utils\config.py) for app/runtime config fields (agent defaults, LLM model/provider/api key env, flags, API base URL).
  - Keep strict validation: if runtime LLM is used and `llm.api_key_env` is missing/empty, fail with typed config error.
- Keep backend settings env-first and align variable naming/docs:
  - [`d:\Projects\clawagent\src\backend\settings.py`](d:\Projects\clawagent\src\backend\settings.py)
  - [`d:\Projects\clawagent\src\backend\app.py`](d:\Projects\clawagent\src\backend\app.py) for workspace/bootstrap env paths.
- Add/refresh `.env.example` with categorized variables:
  - [`d:\Projects\clawagent\.env.example`](d:\Projects\clawagent\.env.example)
  - Include backend core (`CLAW_DATABASE_URL`, `CLAW_REDIS_URL`, `CLAW_WORKSPACE`, bootstrap creds), runtime LLM (`OPENAI_API_KEY` + explicit `llm.api_key_env` docs), limits/timeouts, and feature toggles.
- Ensure dependency availability for dotenv loading (if needed):
  - [`d:\Projects\clawagent\pyproject.toml`](d:\Projects\clawagent\pyproject.toml)

## Tests & Verification
- Add/update config-loading tests for precedence and validation:
  - Env overrides YAML for overlapping keys.
  - Missing `llm.api_key_env` still fails in non-test runtime.
  - Backend and CLI both read `.env` without manual shell exports.
- Run targeted backend/CLI smoke:
  - login/chat flow with `.env` only.
  - failure path shows explicit config error when required env vars are absent.

## Risks To Control
- Avoid breaking existing YAML-only local workflows unexpectedly; preserve clear precedence docs.
- Keep secrets out of committed files (`.env.example` placeholders only).
- Prevent split behavior where backend and CLI load different `.env` paths.