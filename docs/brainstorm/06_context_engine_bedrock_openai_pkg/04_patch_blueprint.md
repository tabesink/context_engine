# 04 — Patch Blueprint

This file gives the coding agent concrete snippets. Treat these as implementation guidance, not a blindly applied patch.

---

## `app/core/config.py`

Add fields inside `Settings` near the existing LightRAG deployment settings.

```python
    # LightRAG model provider configuration. These values are emitted into
    # generated per-domain domain.env files and consumed by LightRAG itself.
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

---

## `app/lightrag_deploy/settings.py`

Add dataclass fields:

```python
    llm_binding: str = "openai"
    llm_binding_host: str | None = None
    llm_binding_api_key: str | None = None
    llm_model: str | None = None

    keyword_llm_model: str | None = None
    query_llm_model: str | None = None
    vlm_llm_model: str | None = None

    embedding_binding: str = "openai"
    embedding_binding_host: str | None = None
    embedding_binding_api_key: str | None = None
    embedding_model: str | None = None
    embedding_dim: int | None = None
    embedding_token_limit: int | None = None
    embedding_send_dim: bool | None = None
    embedding_use_base64: bool | None = None

    openai_llm_max_tokens: int | None = None
    openai_llm_max_completion_tokens: int | None = None
    openai_llm_temperature: float | None = None
    openai_llm_extra_body: str | None = None
```

Update `from_app_settings()`:

```python
            llm_binding=settings.lightrag_llm_binding,
            llm_binding_host=settings.lightrag_llm_binding_host,
            llm_binding_api_key=settings.lightrag_llm_binding_api_key,
            llm_model=settings.lightrag_llm_model,
            keyword_llm_model=settings.lightrag_keyword_llm_model,
            query_llm_model=settings.lightrag_query_llm_model,
            vlm_llm_model=settings.lightrag_vlm_llm_model,
            embedding_binding=settings.lightrag_embedding_binding,
            embedding_binding_host=settings.lightrag_embedding_binding_host,
            embedding_binding_api_key=settings.lightrag_embedding_binding_api_key,
            embedding_model=settings.lightrag_embedding_model,
            embedding_dim=settings.lightrag_embedding_dim,
            embedding_token_limit=settings.lightrag_embedding_token_limit,
            embedding_send_dim=settings.lightrag_embedding_send_dim,
            embedding_use_base64=settings.lightrag_embedding_use_base64,
            openai_llm_max_tokens=settings.lightrag_openai_llm_max_tokens,
            openai_llm_max_completion_tokens=settings.lightrag_openai_llm_max_completion_tokens,
            openai_llm_temperature=settings.lightrag_openai_llm_temperature,
            openai_llm_extra_body=settings.lightrag_openai_llm_extra_body,
```

---

## `app/lightrag_deploy/compose.py`

Add helpers:

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


def _append_provider_env(lines: list[str], settings: LightRAGDeploySettings | None) -> None:
    if settings is None:
        return

    lines.append("")
    lines.append("# Model provider configuration")
    _append_env(lines, "LLM_BINDING", settings.llm_binding)
    _append_env(lines, "LLM_BINDING_HOST", settings.llm_binding_host)
    _append_env(lines, "LLM_BINDING_API_KEY", settings.llm_binding_api_key)
    _append_env(lines, "LLM_MODEL", settings.llm_model)

    _append_env(lines, "KEYWORD_LLM_MODEL", settings.keyword_llm_model)
    _append_env(lines, "QUERY_LLM_MODEL", settings.query_llm_model)
    _append_env(lines, "VLM_LLM_MODEL", settings.vlm_llm_model)

    lines.append("")
    lines.append("# Embedding provider configuration")
    _append_env(lines, "EMBEDDING_BINDING", settings.embedding_binding)
    _append_env(lines, "EMBEDDING_BINDING_HOST", settings.embedding_binding_host)
    _append_env(lines, "EMBEDDING_BINDING_API_KEY", settings.embedding_binding_api_key)
    _append_env(lines, "EMBEDDING_MODEL", settings.embedding_model)
    _append_env(lines, "EMBEDDING_DIM", settings.embedding_dim)
    _append_env(lines, "EMBEDDING_TOKEN_LIMIT", settings.embedding_token_limit)
    _append_env(lines, "EMBEDDING_SEND_DIM", settings.embedding_send_dim)
    _append_env(lines, "EMBEDDING_USE_BASE64", settings.embedding_use_base64)

    lines.append("")
    lines.append("# OpenAI-compatible provider tuning")
    _append_env(lines, "OPENAI_LLM_MAX_TOKENS", settings.openai_llm_max_tokens)
    _append_env(lines, "OPENAI_LLM_MAX_COMPLETION_TOKENS", settings.openai_llm_max_completion_tokens)
    _append_env(lines, "OPENAI_LLM_TEMPERATURE", settings.openai_llm_temperature)
    _append_env(lines, "OPENAI_LLM_EXTRA_BODY", settings.openai_llm_extra_body)
```

Call the helper at the end of `render_domain_env()` before return:

```python
    _append_provider_env(lines, settings)
    return "\n".join(lines) + "\n"
```

---

## Test expectations for `domain.env`

Expected partial output:

```env
# Model provider configuration
LLM_BINDING=openai
LLM_BINDING_HOST=https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1
LLM_BINDING_API_KEY=test-bedrock-key
LLM_MODEL=openai.gpt-oss-20b-1:0

# Embedding provider configuration
EMBEDDING_BINDING=openai
EMBEDDING_BINDING_HOST=https://api.openai.com/v1
EMBEDDING_BINDING_API_KEY=test-openai-key
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIM=3072
EMBEDDING_TOKEN_LIMIT=8192
EMBEDDING_SEND_DIM=false
EMBEDDING_USE_BASE64=true
```

---

## Avoid this anti-pattern

Do not generate this:

```env
OPENAI_API_KEY=<bedrock-key>
OPENAI_BASE_URL=<bedrock-url>
```

Use the LightRAG-native names instead:

```env
LLM_BINDING_API_KEY=<bedrock-key>
LLM_BINDING_HOST=<bedrock-url>
```

