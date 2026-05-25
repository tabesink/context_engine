# Context Engine Implementation Package: LightRAG via Amazon Bedrock OpenAI-Compatible Endpoint

**Audience:** coding agent, junior developer, and reviewer  
**Target repo:** `https://github.com/tabesink/context_engine.git`  
**Date:** 2026-05-25  
**Design choice:** Use Amazon Bedrock's OpenAI-compatible API surface while keeping LightRAG configured with `LLM_BINDING=openai` and `EMBEDDING_BINDING=openai`.

---

## Goal

Update `context_engine` so every generated LightRAG domain receives model-provider configuration from the root `.env` file. The app should support this flow:

```text
Context Engine backend
  └── calls LightRAG domain server using LIGHTRAG_API_KEY / X-API-Key

LightRAG domain server
  └── calls Amazon Bedrock through OpenAI-compatible endpoint
      using LLM_BINDING=openai
      using LLM_BINDING_HOST=https://bedrock-runtime.<region>.amazonaws.com/openai/v1
      using LLM_BINDING_API_KEY=<Amazon Bedrock API key>
```

This package intentionally does **not** switch LightRAG to native `LLM_BINDING=bedrock`. The chosen approach is to keep LightRAG on its OpenAI-compatible binding and point it at the Bedrock OpenAI-compatible base URL.

---

## Package contents

| File | Purpose |
|---|---|
| `01_architecture_decision.md` | Explains the chosen architecture and why. |
| `02_env_contract.md` | Defines exact environment variables to add. |
| `03_implementation_steps.md` | File-by-file implementation instructions. |
| `04_patch_blueprint.md` | Concrete code snippets/pseudodiff for the coding agent. |
| `05_test_plan.md` | Required unit/integration tests and acceptance checks. |
| `06_coding_agent_prompt.md` | Copy-paste prompt for a coding agent. |
| `07_manual_validation_checklist.md` | Manual verification steps after implementation. |

---

## Important terminology

### `LIGHTRAG_API_KEY`

This is the **server-to-server API key** used by `context_engine` when it calls the LightRAG HTTP server. It is sent as `X-API-Key`.

It is **not** the OpenAI key and it is **not** the Bedrock API key.

### `LIGHTRAG_LLM_BINDING_API_KEY`

This is the provider key that LightRAG uses to call the configured LLM backend. For this implementation, it should contain an **Amazon Bedrock API key**, because the OpenAI-compatible Bedrock endpoint accepts a Bedrock API key as the OpenAI-style bearer token.

### `LIGHTRAG_LLM_BINDING_HOST`

For Bedrock OpenAI-compatible Chat Completions, this should be:

```env
LIGHTRAG_LLM_BINDING_HOST=https://bedrock-runtime.<region>.amazonaws.com/openai/v1
```

Example:

```env
LIGHTRAG_LLM_BINDING_HOST=https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1
```

---

## Non-goals

Do not implement these unless separately requested:

- Do not add local embeddings back into `context_engine`.
- Do not make `context_engine` directly call Bedrock for retrieval or generation.
- Do not switch to LightRAG native `LLM_BINDING=bedrock`.
- Do not store provider secrets in `domains.json`.
- Do not expose provider keys through public or admin API responses.
- Do not hand-edit generated `domain.env` files as the primary solution.

