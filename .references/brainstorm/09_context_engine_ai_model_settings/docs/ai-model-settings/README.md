# AI Model Settings Documentation Package

Generated: 2026-05-26

This package describes the implementation plan for adding an **admin-only AI Models settings shell** to `context_engine`.

The feature lets an admin select default LLM and embedding profiles, then uses those profiles in LightRAG domain creation and other backend workflows.

## Core Decision

Embedding model selection is **domain-locked**.

LLM selection is **default-driven and changeable**.

```text
Admin Settings
  → AI Models
      → default LLM profile
      → default embedding profile
      → allowed embedding profiles
  → Create Knowledge Graph / LightRAG Domain
      → choose embedding profile once
      → persist immutable embedding snapshot on domain
      → generate LightRAG domain.env from that snapshot
```

## Files in This Package

- `FEATURE_SPEC.md` — product behavior and UX rules.
- `BACKEND_IMPLEMENTATION.md` — API, schema, services, migrations, validation.
- `FRONTEND_IMPLEMENTATION.md` — settings shell UI, admin-only flows, domain creation UX.
- `LIGHTRAG_DOMAIN_MODEL_RULES.md` — embedding immutability and domain.env generation.
- `CODING_AGENT_TASKS.md` — task-sized implementation plan.
- `ADRS_TO_WRITE.md` — architecture decisions to preserve.
- `RESEARCH_NOTES.md` — official-doc notes and source links.

## Recommended Implementation Order

1. Add backend schema and service layer for AI model profiles.
2. Add admin-only API routes.
3. Extend LightRAG domain model with immutable embedding snapshot.
4. Update domain.env generation.
5. Add frontend settings shell route: `Settings → AI Models`.
6. Add embedding dropdown to Knowledge Graph / LightRAG domain creation.
7. Add tests and migration.
