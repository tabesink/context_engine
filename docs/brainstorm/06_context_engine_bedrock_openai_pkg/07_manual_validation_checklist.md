# 07 — Manual Validation Checklist

## 1. Configure root `.env`

```env
LIGHTRAG_ENABLED=true
LIGHTRAG_DEPLOY_ENABLED=true

# Context Engine -> LightRAG server auth
LIGHTRAG_API_KEY=change-this-server-api-key

# LightRAG -> Bedrock OpenAI-compatible LLM
LIGHTRAG_LLM_BINDING=openai
LIGHTRAG_LLM_BINDING_HOST=https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1
LIGHTRAG_LLM_BINDING_API_KEY=<your-bedrock-api-key>
LIGHTRAG_LLM_MODEL=openai.gpt-oss-20b-1:0

# LightRAG -> embeddings
LIGHTRAG_EMBEDDING_BINDING=openai
LIGHTRAG_EMBEDDING_BINDING_HOST=https://api.openai.com/v1
LIGHTRAG_EMBEDDING_BINDING_API_KEY=<your-openai-api-key>
LIGHTRAG_EMBEDDING_MODEL=text-embedding-3-large
LIGHTRAG_EMBEDDING_DIM=3072
LIGHTRAG_EMBEDDING_TOKEN_LIMIT=8192
LIGHTRAG_EMBEDDING_SEND_DIM=false
LIGHTRAG_EMBEDDING_USE_BASE64=true
```

## 2. Run focused tests

```bash
pytest tests/test_lightrag_deploy_settings.py tests/test_lightrag_deploy_manifest_compose.py
```

## 3. Regenerate a LightRAG domain

Use the TUI or admin API to create/regenerate a domain.

Then inspect:

```bash
cat .data/lightrag/domains/<domain_id>/domain.env
```

Expected:

```env
LLM_BINDING=openai
LLM_BINDING_HOST=https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1
LLM_BINDING_API_KEY=<your-bedrock-api-key>
LLM_MODEL=openai.gpt-oss-20b-1:0
```

## 4. Confirm secrets are not in manifest or compose

```bash
grep -R "<your-bedrock-api-key>" \
  .data/lightrag/domains.json \
  .data/lightrag/docker-compose.lightrag-domains.yml
```

Expected: no output.

```bash
grep -R "<your-bedrock-api-key>" .data/lightrag/domains/*/domain.env
```

Expected: one or more `domain.env` matches only.

## 5. Restart LightRAG domain service

```bash
docker compose -f .data/lightrag/docker-compose.lightrag-domains.yml up -d --force-recreate <service_name>
```

Or use the admin domain recreate endpoint/TUI action.

## 6. Confirm env inside container

```bash
docker exec -it context_engine_lightrag_<domain_id> sh -lc 'printenv | grep -E "LLM_BINDING|EMBEDDING_BINDING|LLM_MODEL|EMBEDDING_MODEL"'
```

Expected values include:

```text
LLM_BINDING=openai
LLM_BINDING_HOST=https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1
LLM_MODEL=openai.gpt-oss-20b-1:0
```

## 7. Upload a small document

Use admin upload.

Expected:

- Document row is created.
- LightRAG ingest job is queued.
- Worker calls LightRAG domain.
- LightRAG domain uses Bedrock-compatible LLM endpoint for extraction/querying.

## 8. Query the document

Use:

```bash
POST /query/answer
```

Expected:

- Context Engine calls LightRAG successfully.
- LightRAG returns retrieval/answer result.
- No provider API key appears in API responses or logs.

## 9. Common failures

### 401/403 from Bedrock endpoint

Likely causes:

- `LIGHTRAG_LLM_BINDING_API_KEY` is not a Bedrock API key.
- API key is for the wrong AWS account/region/project.
- Region endpoint does not match the enabled model region.

### 404/model not found

Likely causes:

- `LIGHTRAG_LLM_MODEL` is not available in that region.
- Model access has not been enabled in Amazon Bedrock.
- Endpoint path is wrong.

### Embedding failure

Likely causes:

- Embedding host/model does not support OpenAI-compatible embedding calls.
- Embedding dimension does not match the model.
- Existing LightRAG index was created with a different embedding dimension.

If embedding model/dim changes after indexing, rebuild the LightRAG domain index.

