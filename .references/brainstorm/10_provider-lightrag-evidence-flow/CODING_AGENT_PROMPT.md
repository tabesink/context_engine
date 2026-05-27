# Coding Agent Prompt

Use this prompt when handing the repo to a coding agent.

```md
You are a senior full-stack coding agent working in `context_engine`.

Goal:
Implement the provider-centered LightRAG ingestion and evidence flow:

Admin configures Provider in Settings
  → admin creates/selects LightRAG domain
  → domain stores provider + embedding model identity
  → admin uploads document to domain
  → backend ingests local structure/assets and LightRAG chunks
  → regular users ask questions through chat
  → backend `/retrieve` returns stable evidence
  → frontend workspace tree and context panel render evidence

Before coding:
1. Read docs/provider-lightrag-evidence-flow/README.md.
2. Read EXECUTIVE_SUMMARY.md.
3. Read IMPLEMENTATION_PLAN.md.
4. Read CONCRETE_CODING_TASKS.md.
5. Run current backend/frontend tests.

Non-negotiables:
- Do not expose raw provider API keys.
- Do not let regular users modify providers, domains, or documents.
- Do not allow embedding model changes on a domain with ingested documents.
- Do not add duplicate query APIs unless explicitly approved.
- Prefer `/retrieve` as canonical evidence API.
- Keep LightRAG behind adapter/service boundaries.
- Keep changes incremental and test-backed.

Implementation order:
1. Rename settings route to Provider.
2. Add provider profile backend model/API.
3. Add secure secret redaction.
4. Link provider profile to LightRAG domain creation/env generation.
5. Enforce embedding lock.
6. Harden upload/ingestion validation.
7. Align chat with `/retrieve`.
8. Add RetrieveResponse → ContextPanel adapter.
9. Wire workspace tree endpoint.
10. Add tests and ADRs.
```
