# easy-deploy-lightrag Codebase Documentation Package

Generated: 2026-05-18  
Repository reviewed: `https://github.com/tabesink/easy-deploy-lightrag.git`

## Scope

This documentation package maps the current visible codebase structure, runtime surfaces, API routes, CLI commands, storage model, LightRAG integration points, tests, and known implementation risks.

The repo appears to be a hybrid system, not only a thin deployment script. It contains:

- A Typer/Rich CLI for domain deployment and local orchestration.
- Docker Compose configuration for PostgreSQL/pgvector, Redis, Neo4j, and one or more LightRAG domain containers.
- A minimal FastAPI backend under `src/server` for auth, user management, conversations, LightRAG domain discovery, and graph proxy routes.
- A Next.js client under `client/`.
- A vendored/modified LightRAG implementation under `src/lightrag` and a LightRAG WebUI under `src/lightrag_webui`.
- Tests that appear to cover both current and possibly older backend namespace assumptions.

## Important Review Limitation

The local sandbox could not clone GitHub because DNS resolution for `github.com` failed. The documentation was therefore generated from GitHub web/raw inspection of the public repository files and directory listings. It is still grounded in observed file paths, function names, classes, routes, and config content, but a final local clone review should be run before editing production code.

## Files in This Package

| File | Purpose |
|---|---|
| `01_Executive_Summary_and_Architecture.md` | Practical summary, architecture diagram, runtime component map. |
| `02_API_Surface_Map.md` | FastAPI route map, auth/admin/conversation/LightRAG proxy surfaces. |
| `03_CLI_and_Deployment_Surface.md` | CLI commands, Docker Compose model, deployment lifecycle, environment variables. |
| `04_Data_Model_and_Persistence.md` | SQLite schema, repositories, domain storage, Docker volumes, artifact persistence. |
| `05_Functional_Workflows.md` | End-to-end workflows for local start, domain deploy, ingest/index, chat, graph, delete. |
| `06_Frontend_and_LightRAG_Integration.md` | Next.js client, stores, graph UI, LightRAG web UI, structural chunking. |
| `07_Tests_Risks_and_Agent_Safety.md` | Test coverage, namespace mismatches, risks, junior-dev/coding-agent safety checklist. |

## How to Use This Package

Start with files `01` through `03` to understand the major runtime shape. Then read `04` and `05` before touching storage, Docker, or domain lifecycle code. Use `07` as the safety checklist before giving a coding agent implementation instructions.
