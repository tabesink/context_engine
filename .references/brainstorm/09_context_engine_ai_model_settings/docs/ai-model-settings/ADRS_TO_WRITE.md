# ADRs to Write

## ADR: AI Model Settings and Domain Embedding Lock

### Decision

The app stores admin-selectable AI model profiles.

Embedding profiles are immutable per LightRAG domain after creation.

LLM defaults can be changed.

### Context

Embedding vectors from different models are not compatible inside the same vector index. LightRAG also requires the embedding model and dimension to be decided before indexing.

### Consequences

- Domain creation must snapshot embedding profile.
- Domain upload must use domain embedding profile.
- Existing domains do not automatically change when admin changes default embedding.
- To change embedding model, rebuild/recreate domain.
- LLM changes can be applied more flexibly.

## ADR: Secrets Stay in Environment, Not Browser

### Decision

The admin UI can select profiles and show secret status, but it cannot read or write raw API keys in V1.

### Consequences

- Safer implementation.
- Less risk of accidental secret disclosure.
- Admin must configure keys in `.env` or deployment secret manager.

## ADR: Provider Scope for V1

### Decision

V1 exposes:

- OpenAI LLM
- AWS Bedrock OpenAI-compatible LLM
- Ollama LLM
- OpenAI embeddings
- Ollama embeddings

### Consequences

- Bedrock native embeddings are deferred.
- Future native Bedrock embeddings require separate adapter and UI profile type.
