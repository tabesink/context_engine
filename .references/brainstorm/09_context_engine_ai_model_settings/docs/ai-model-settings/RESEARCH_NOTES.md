# Research Notes

## OpenAI Embeddings

OpenAI's docs describe `text-embedding-3-small` and `text-embedding-3-large` as current embedding models. Defaults:

- `text-embedding-3-small`: 1536 dimensions
- `text-embedding-3-large`: 3072 dimensions
- both list 8192 max input in the OpenAI embeddings guide

Source:

- https://developers.openai.com/api/docs/guides/embeddings

## Ollama OpenAI Compatibility

Ollama documents partial OpenAI API compatibility and supports:

- `/v1/chat/completions`
- `/v1/responses`
- `/v1/models`
- `/v1/embeddings`

For local OpenAI SDK compatibility, the API key is required by SDK shape but ignored by Ollama.

Source:

- https://docs.ollama.com/api/openai-compatibility

## AWS Bedrock OpenAI-Compatible APIs

Amazon Bedrock documents OpenAI-compatible Chat Completions and Responses APIs. The OpenAI SDK must point to the Bedrock endpoint and use an Amazon Bedrock API key.

Examples:

- Chat Completions endpoint: `https://bedrock-runtime.<region>.amazonaws.com/openai/v1`
- Responses API endpoint: `https://bedrock-mantle.<region>.api.aws/v1`

Sources:

- https://docs.aws.amazon.com/bedrock/latest/userguide/inference-chat-completions.html
- https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-mantle.html

## Bedrock Embeddings

Amazon Bedrock has native embedding models such as Titan Text Embeddings V2. These are not the same as exposing OpenAI `/v1/embeddings` through the Bedrock OpenAI-compatible path.

Source:

- https://docs.aws.amazon.com/bedrock/latest/userguide/titan-embedding-models.html

## LightRAG Provider and Embedding Rules

LightRAG docs state that LLM and embedding providers must be configured before server startup and that LightRAG supports OpenAI-compatible, Ollama, Bedrock, and other bindings. The LightRAG README also warns that the embedding model must be determined before document indexing and the same model must be used during query; for storage like PostgreSQL, vector dimensions are defined at table creation.

Sources:

- https://github.com/HKUDS/LightRAG/blob/main/docs/LightRAG-API-Server.md
- https://github.com/HKUDS/LightRAG
- https://github.com/HKUDS/LightRAG/blob/main/env.example
