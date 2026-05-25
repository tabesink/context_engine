# 05 — Test Plan

## Unit tests to update

### `tests/test_lightrag_deploy_settings.py`

Add new required keys to `test_env_example_declares_lightrag_deployment_settings()`:

```python
"LIGHTRAG_LLM_BINDING",
"LIGHTRAG_LLM_BINDING_HOST",
"LIGHTRAG_LLM_BINDING_API_KEY",
"LIGHTRAG_LLM_MODEL",
"LIGHTRAG_KEYWORD_LLM_MODEL",
"LIGHTRAG_QUERY_LLM_MODEL",
"LIGHTRAG_VLM_LLM_MODEL",
"LIGHTRAG_EMBEDDING_BINDING",
"LIGHTRAG_EMBEDDING_BINDING_HOST",
"LIGHTRAG_EMBEDDING_BINDING_API_KEY",
"LIGHTRAG_EMBEDDING_MODEL",
"LIGHTRAG_EMBEDDING_DIM",
"LIGHTRAG_EMBEDDING_TOKEN_LIMIT",
"LIGHTRAG_EMBEDDING_SEND_DIM",
"LIGHTRAG_EMBEDDING_USE_BASE64",
"LIGHTRAG_OPENAI_LLM_MAX_TOKENS",
"LIGHTRAG_OPENAI_LLM_MAX_COMPLETION_TOKENS",
"LIGHTRAG_OPENAI_LLM_TEMPERATURE",
"LIGHTRAG_OPENAI_LLM_EXTRA_BODY",
```

Update `test_settings_parse_lightrag_deployment_fields()` with sample values:

```python
settings = Settings(
    lightrag_llm_binding="openai",
    lightrag_llm_binding_host="https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1",
    lightrag_llm_binding_api_key="test-bedrock-key",
    lightrag_llm_model="openai.gpt-oss-20b-1:0",
    lightrag_embedding_binding="openai",
    lightrag_embedding_binding_host="https://api.openai.com/v1",
    lightrag_embedding_binding_api_key="test-openai-key",
    lightrag_embedding_model="text-embedding-3-large",
    lightrag_embedding_dim=3072,
    lightrag_embedding_token_limit=8192,
    lightrag_embedding_send_dim=False,
    lightrag_embedding_use_base64=True,
)
```

Then assert mappings:

```python
assert deploy.llm_binding == "openai"
assert deploy.llm_binding_host == "https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1"
assert deploy.llm_binding_api_key == "test-bedrock-key"
assert deploy.llm_model == "openai.gpt-oss-20b-1:0"
assert deploy.embedding_model == "text-embedding-3-large"
assert deploy.embedding_dim == 3072
```

---

### `tests/test_lightrag_deploy_manifest_compose.py`

Add a helper settings variant:

```python
def _settings_with_provider(tmp_path: Path) -> LightRAGDeploySettings:
    settings = _settings(tmp_path)
    return replace(
        settings,
        llm_binding="openai",
        llm_binding_host="https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1",
        llm_binding_api_key="test-bedrock-key",
        llm_model="openai.gpt-oss-20b-1:0",
        embedding_binding="openai",
        embedding_binding_host="https://api.openai.com/v1",
        embedding_binding_api_key="test-openai-key",
        embedding_model="text-embedding-3-large",
        embedding_dim=3072,
        embedding_token_limit=8192,
        embedding_send_dim=False,
        embedding_use_base64=True,
    )
```

You may need:

```python
from dataclasses import replace
```

Add test:

```python
def test_domain_env_includes_bedrock_openai_compatible_provider_config(tmp_path: Path) -> None:
    settings = _settings_with_provider(tmp_path)
    paths = DomainPathResolver(settings).ensure_domain_paths("fatigue")
    domain = _domain(tmp_path)

    write_domain_env(domain, settings, paths)

    output = paths.env_file.read_text(encoding="utf-8")
    assert "LLM_BINDING=openai" in output
    assert "LLM_BINDING_HOST=https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1" in output
    assert "LLM_BINDING_API_KEY=test-bedrock-key" in output
    assert "LLM_MODEL=openai.gpt-oss-20b-1:0" in output
    assert "EMBEDDING_BINDING=openai" in output
    assert "EMBEDDING_BINDING_HOST=https://api.openai.com/v1" in output
    assert "EMBEDDING_BINDING_API_KEY=test-openai-key" in output
    assert "EMBEDDING_MODEL=text-embedding-3-large" in output
    assert "EMBEDDING_DIM=3072" in output
    assert "EMBEDDING_SEND_DIM=false" in output
    assert "EMBEDDING_USE_BASE64=true" in output
```

Add secret non-leakage test:

```python
def test_provider_secrets_are_not_written_to_manifest_or_compose(tmp_path: Path) -> None:
    settings = _settings_with_provider(tmp_path)
    domain = _domain(tmp_path)

    compose = ComposeGenerator(settings).render([domain])
    assert "test-bedrock-key" not in compose
    assert "test-openai-key" not in compose

    store = DomainManifestStore(settings.manifest_path)
    store.add_domain(domain)
    manifest = settings.manifest_path.read_text(encoding="utf-8")
    assert "test-bedrock-key" not in manifest
    assert "test-openai-key" not in manifest
```

---

## Manual tests

### Generate env and inspect it

```bash
docker compose run --rm api python - <<'PY'
from app.core.config import get_settings
from app.lightrag_deploy.settings import LightRAGDeploySettings
from app.lightrag_deploy.compose import render_domain_env
print(LightRAGDeploySettings.from_app_settings(get_settings()))
PY
```

Then create/regenerate a LightRAG domain through the admin API/TUI and inspect:

```bash
cat .data/lightrag/domains/<domain_id>/domain.env
```

### Smoke test Bedrock endpoint from host

Use an API key with Bedrock OpenAI-compatible access:

```bash
export BEDROCK_OPENAI_BASE_URL="https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1"
export BEDROCK_API_KEY="your-bedrock-api-key"

curl -X POST "$BEDROCK_OPENAI_BASE_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BEDROCK_API_KEY" \
  -d '{
    "model": "openai.gpt-oss-20b-1:0",
    "messages": [{"role": "user", "content": "Say hello in one sentence."}]
  }'
```

### Smoke test from inside LightRAG container

```bash
docker exec -it context_engine_lightrag_<domain_id> sh
printenv | grep -E 'LLM_BINDING|EMBEDDING_BINDING|LLM_MODEL|EMBEDDING_MODEL'
```

Expected:

```text
LLM_BINDING=openai
LLM_BINDING_HOST=https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1
LLM_MODEL=openai.gpt-oss-20b-1:0
```

Do not print real keys in shared logs/screenshots.

