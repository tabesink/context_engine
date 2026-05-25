# 03 — Implementation Steps

## Step 1 — Add settings to `app/core/config.py`

Add provider fields to `Settings`.

Required new fields:

```python
lightrag_llm_binding: str = "openai"
lightrag_llm_binding_host: str | None = None
lightrag_llm_binding_api_key: str | None = None
lightrag_llm_model: str | None = None

lightrag_keyword_llm_model: str | None = None
lightrag_query_llm_model: str | None = None
lightrag_vlm_llm_model: str | None = None

lightrag_embedding_binding: str = "openai"
lightrag_embedding_binding_host: str | None = None
lightrag_embedding_binding_api_key: str | None = None
lightrag_embedding_model: str | None = None
lightrag_embedding_dim: int | None = None
lightrag_embedding_token_limit: int | None = None
lightrag_embedding_send_dim: bool | None = None
lightrag_embedding_use_base64: bool | None = None

lightrag_openai_llm_max_tokens: int | None = None
lightrag_openai_llm_max_completion_tokens: int | None = None
lightrag_openai_llm_temperature: float | None = None
lightrag_openai_llm_extra_body: str | None = None
```

Keep `extra="ignore"` so older env files do not break.

## Step 2 — Add provider fields to `app/lightrag_deploy/settings.py`

Extend `LightRAGDeploySettings` with matching fields, but remove the `lightrag_` prefix in the dataclass field names for readability.

Example:

```python
llm_binding: str = "openai"
llm_binding_host: str | None = None
llm_binding_api_key: str | None = None
llm_model: str | None = None
```

Then update `from_app_settings()` to map from `Settings` to `LightRAGDeploySettings`.

## Step 3 — Update `app/lightrag_deploy/compose.py`

Modify `render_domain_env()` so it writes provider settings after storage settings.

Implementation rule:

- Write all non-secret non-empty values normally.
- Write secret keys only to `domain.env`, never to compose labels, manifest, logs, or API responses.
- Skip blank/None values.
- Convert booleans to lowercase strings only if LightRAG expects lowercase, otherwise use Python string form consistently. Safer for env files: `true` / `false`.

Suggested helper:

```python
def _append_env(lines: list[str], key: str, value: object | None) -> None:
    if value is None:
        return
    if isinstance(value, str) and not value.strip():
        return
    if isinstance(value, bool):
        rendered = "true" if value else "false"
    else:
        rendered = str(value)
    lines.append(f"{key}={rendered}")
```

Then add provider variables like:

```python
_append_env(lines, "LLM_BINDING", settings.llm_binding)
_append_env(lines, "LLM_BINDING_HOST", settings.llm_binding_host)
_append_env(lines, "LLM_BINDING_API_KEY", settings.llm_binding_api_key)
_append_env(lines, "LLM_MODEL", settings.llm_model)
```

## Step 4 — Update `.env.example`

Add the full model provider section from `02_env_contract.md`.

Important: clearly document that `LIGHTRAG_LLM_BINDING_API_KEY` is the Bedrock provider key when using the Bedrock OpenAI-compatible endpoint.

## Step 5 — Update tests

Update these files:

```text
tests/test_lightrag_deploy_settings.py
tests/test_lightrag_deploy_manifest_compose.py
```

Required test cases:

1. `.env.example` declares new provider keys.
2. `Settings` parses provider keys.
3. `LightRAGDeploySettings.from_app_settings()` maps provider keys.
4. `render_domain_env()` emits provider settings.
5. `render_domain_env()` skips blank optional values.
6. `domains.json` does not contain provider secret values.
7. Compose output references `env_file` but does not inline provider secrets.

## Step 6 — Manual validation

Run:

```bash
pytest tests/test_lightrag_deploy_settings.py tests/test_lightrag_deploy_manifest_compose.py
```

Then create/regenerate a domain and inspect:

```bash
cat .data/lightrag/domains/<domain_id>/domain.env
```

Expected:

```env
LLM_BINDING=openai
LLM_BINDING_HOST=https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1
LLM_BINDING_API_KEY=<bedrock-api-key>
LLM_MODEL=openai.gpt-oss-20b-1:0
```

## Step 7 — Do not leak secrets

Search generated files:

```bash
grep -R "your-bedrock-api-key" .data/lightrag/domains.json .data/lightrag/docker-compose.lightrag-domains.yml
```

Expected: no matches.

Search domain env:

```bash
grep -R "your-bedrock-api-key" .data/lightrag/domains/*/domain.env
```

Expected: matches only in `domain.env`.

