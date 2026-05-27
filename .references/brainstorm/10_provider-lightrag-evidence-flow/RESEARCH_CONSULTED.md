# Research Consulted

The coding agent should verify these official references before implementation, especially because provider APIs and LightRAG behavior can change.

| Source | Why Consulted | Relevant Takeaway |
|---|---|---|
| LightRAG official repository/docs | Confirm LightRAG server/API/WebUI and provider/runtime behavior | Keep LightRAG as remote service boundary; do not duplicate internals |
| Ollama OpenAI compatibility docs | Confirm local OpenAI-compatible base URL behavior | Ollama can be represented as OpenAI-compatible provider with local base URL |
| AWS Bedrock OpenAI-compatible docs | Confirm Bedrock OpenAI-compatible endpoint behavior | Bedrock-compatible provider can fit base URL + credential + model shape |
| FastAPI security docs | Confirm bearer-token/admin route pattern | Keep provider/domain/document writes behind admin dependency |
| SQLAlchemy/Alembic docs | Confirm migration discipline | Provider profile/domain fields need migrations and tests |
| Next.js routing docs | Confirm settings route/page changes | Rename route/UI in a way consistent with app router structure |
