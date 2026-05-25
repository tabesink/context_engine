# 06 — Coding Agent Prompt

Use this prompt with a coding agent.

```text
You are a senior Python/FastAPI engineer working in the repo:
https://github.com/tabesink/context_engine.git

Task: Implement LightRAG model-provider env generation for Amazon Bedrock's OpenAI-compatible endpoint.

Context:
- context_engine already has LightRAG domain deployment support under app/lightrag_deploy/*.
- app/core/config.py currently contains LIGHTRAG API/deployment/storage settings.
- app/lightrag_deploy/compose.py currently generates per-domain domain.env files, but only includes runtime/storage/Postgres settings.
- The goal is to keep LightRAG configured with LLM_BINDING=openai and point LLM_BINDING_HOST at Amazon Bedrock's OpenAI-compatible endpoint.
- Do not switch to native LLM_BINDING=bedrock.
- Do not add local embeddings to context_engine.
- Do not make context_engine call Bedrock directly.

Implement:
1. Add these root env settings to app/core/config.py Settings:
   - lightrag_llm_binding
   - lightrag_llm_binding_host
   - lightrag_llm_binding_api_key
   - lightrag_llm_model
   - lightrag_keyword_llm_model
   - lightrag_query_llm_model
   - lightrag_vlm_llm_model
   - lightrag_embedding_binding
   - lightrag_embedding_binding_host
   - lightrag_embedding_binding_api_key
   - lightrag_embedding_model
   - lightrag_embedding_dim
   - lightrag_embedding_token_limit
   - lightrag_embedding_send_dim
   - lightrag_embedding_use_base64
   - lightrag_openai_llm_max_tokens
   - lightrag_openai_llm_max_completion_tokens
   - lightrag_openai_llm_temperature
   - lightrag_openai_llm_extra_body

2. Add matching fields to LightRAGDeploySettings in app/lightrag_deploy/settings.py and map them in from_app_settings().

3. Update app/lightrag_deploy/compose.py so render_domain_env() emits non-empty provider variables into generated domain.env using LightRAG's native variable names:
   - LLM_BINDING
   - LLM_BINDING_HOST
   - LLM_BINDING_API_KEY
   - LLM_MODEL
   - KEYWORD_LLM_MODEL
   - QUERY_LLM_MODEL
   - VLM_LLM_MODEL
   - EMBEDDING_BINDING
   - EMBEDDING_BINDING_HOST
   - EMBEDDING_BINDING_API_KEY
   - EMBEDDING_MODEL
   - EMBEDDING_DIM
   - EMBEDDING_TOKEN_LIMIT
   - EMBEDDING_SEND_DIM
   - EMBEDDING_USE_BASE64
   - OPENAI_LLM_MAX_TOKENS
   - OPENAI_LLM_MAX_COMPLETION_TOKENS
   - OPENAI_LLM_TEMPERATURE
   - OPENAI_LLM_EXTRA_BODY

4. Update .env.example with a clear LightRAG model-provider section. Include a Bedrock OpenAI-compatible example:
   LIGHTRAG_LLM_BINDING=openai
   LIGHTRAG_LLM_BINDING_HOST=https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1
   LIGHTRAG_LLM_BINDING_API_KEY=
   LIGHTRAG_LLM_MODEL=openai.gpt-oss-20b-1:0

5. Update tests:
   - tests/test_lightrag_deploy_settings.py
   - tests/test_lightrag_deploy_manifest_compose.py

6. Security requirements:
   - Provider API keys may appear in generated domain.env only.
   - Provider API keys must not appear in domains.json.
   - Provider API keys must not appear in generated docker-compose output.
   - Do not expose provider keys through any API response.

7. Keep code simple and junior-readable. Avoid broad refactors.

Run:
pytest tests/test_lightrag_deploy_settings.py tests/test_lightrag_deploy_manifest_compose.py

Acceptance criteria:
- New env vars parse from Settings.
- LightRAGDeploySettings maps them correctly.
- Generated domain.env includes LLM/embedding provider config.
- Compose and manifest do not leak provider secrets.
- Existing tests still pass.
```

