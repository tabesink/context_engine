Based on the docs, the important constraint is: keep `ragcli` thin for backend API calls, preserve stable `human|json` output, never leak credentials, and only add real commands where behavior exists. The uploaded CLI docs say `ragcli` is intentionally a thin FastAPI client, with backend business rules kept in the backend; the LightRAG docs say `context_engine` must stay HTTP-only and not copy/import LightRAG internals.   

Use this as the **planning prompt** first:

````markdown
# Planning Task: Add LightRAG Domain Deployment Commands to `context_engine` CLI

## Role

You are a senior software architect and coding agent. Your job is to inspect the current codebase, understand the existing CLI architecture, compare it with the LightRAG deployment CLI in `easy-deploy-lightrag`, and produce a lean implementation plan only.

Do not implement yet. Do not modify files yet. First produce a clear, junior-developer-friendly plan.

---

## Repositories To Inspect

1. `context_engine`
   - GitHub: https://github.com/tabesink/context_engine.git
   - Focus areas:
     - `cli/main.py`
     - `cli/api_client.py`
     - `cli/credentials.py`
     - `docs/cli_docs/*`
     - `scripts/*`
     - LightRAG integration docs and any new `external/lightrag` or `app/integrations/lightrag_*` files

2. `easy-deploy-lightrag`
   - GitHub: https://github.com/tabesink/easy-deploy-lightrag.git
   - Focus areas:
     - `cli/main.py`
     - `scripts/deploy_wizard.sh`
     - `docker-compose.domains.yml`
     - `Dockerfile.lightrag-local`
     - `data/domains.json`
     - `data/base.env`
     - domain lifecycle logic: add, list, up, down, remove, recreate, status, regen, setup wizard

---

## Current Context

`context_engine` has expanded to include a lightweight LightRAG retrieval integration. The app remains the multi-user context orchestration layer. LightRAG remains the retrieval/index/graph engine.

The existing `ragcli` in `context_engine` is a thin CLI client for the FastAPI backend. It currently handles auth, documents, retrieval, admin document actions, and jobs.

The `easy-deploy-lightrag` repo has a working LightRAG deployment CLI and `deploy_wizard.sh` wrapper that manages local/domain-based LightRAG deployments.

The goal is to add the useful LightRAG domain deployment and lifecycle capabilities from `easy-deploy-lightrag` into the `context_engine` CLI in a lean, maintainable way.

---

## Core Objective

Create a plan to extend `context_engine`'s `ragcli` with LightRAG domain deployment and management commands while keeping the codebase:

- lean
- modular
- easy for a junior developer to follow
- low entropy
- testable
- explicit about local operator commands vs backend API commands

---

## Critical Architecture Boundary

Do not tangle LightRAG deployment logic into the existing backend API command code.

Separate the CLI into two clear command families:

1. Backend API commands:
   - auth
   - documents
   - query
   - admin documents
   - jobs
   - graph proxy commands if backend routes exist

2. Local LightRAG operator commands:
   - domain setup
   - domain add
   - domain list
   - domain up
   - domain down
   - domain remove/delete
   - domain recreate
   - domain status
   - domain regen
   - deployment wizard wrapper

Backend API commands use `ApiClient`, auth token, `--api-base-url`, and backend authorization.

Local LightRAG operator commands manage local files, domain manifests, Docker Compose, and wrapper scripts. They should not require `ragcli login` unless they call the `context_engine` backend.

---

## Hard Constraints

Follow these constraints:

1. Keep `ragcli` thin.
   - Do not move backend business rules into the CLI.
   - Do not duplicate backend authorization logic.
   - Admin API authorization remains owned by the backend.

2. Preserve existing CLI contracts.
   - Do not break existing commands.
   - Preserve `--output human|json`.
   - JSON output must remain stable.
   - Existing unsupported backend commands must continue returning `not_supported_by_backend`.

3. Preserve credential safety.
   - Never print access tokens.
   - Never print passwords.
   - Never print API keys.
   - Do not echo sensitive headers.
   - Deployment commands must not print secrets from `.env` files.

4. Keep LightRAG integration modular.
   - Do not import LightRAG internals into `app/`.
   - Keep LightRAG retrieval behind `LightRAGRemoteAdapter`.
   - Keep deployment/runtime concerns separate from retrieval API concerns.

5. Prefer a small module split instead of expanding one huge CLI file.
   - Consider `cli/commands/api.py`
   - Consider `cli/commands/lightrag_domains.py`
   - Consider `cli/lightrag_deploy.py`
   - Consider `cli/output.py`
   - Consider `cli/errors.py`
   - Keep the final structure simple enough for a junior dev.

6. Use TDD-style vertical slices.
   - Add one behavior at a time.
   - Mock subprocess/Docker calls in tests.
   - Do not require live Docker, Postgres, Redis, Neo4j, or LightRAG in unit tests.

---

## Required Planning Work

Before proposing changes, inspect both repositories and produce:

### 1. Existing CLI Map

Map the current `context_engine` CLI:

- command groups
- files/modules
- current auth/session flow
- current API client behavior
- current error/output behavior
- current test coverage
- commands that are real vs backend gaps

### 2. Easy Deploy CLI Capability Inventory

Map the useful capabilities in `easy-deploy-lightrag`:

- `setup`
- `tui`
- `chat`, if still relevant
- `domain add`
- `domain list`
- `domain up`
- `domain down`
- `domain remove`
- `domain recreate`
- `domain status`
- `domain regen`
- `deploy_wizard.sh`
- generated files and directories
- secrets/env files
- Docker Compose generation
- health checks
- domain archive/delete behavior

For each capability, classify it as:

- copy/adapt into `context_engine`
- wrap via script
- defer
- remove/not needed

### 3. Proposed `ragcli` Command Surface

Design the new command surface.

Prefer something like:

```bash
ragcli lightrag setup
ragcli lightrag domain add NAME --port PORT
ragcli lightrag domain list
ragcli lightrag domain up [NAME]
ragcli lightrag domain down [NAME]
ragcli lightrag domain remove NAME
ragcli lightrag domain recreate [NAME]
ragcli lightrag domain status [NAME] --wait
ragcli lightrag domain regen
````

Also consider whether a wrapper command is useful:

```bash
ragcli lightrag wizard
```

or whether `scripts/deploy-lightrag.sh` should simply invoke:

```bash
python -m cli.main lightrag ...
```

Explain your recommendation.

### 4. Local Operator Command Design

For each proposed LightRAG command, specify:

* command name
* source behavior from `easy-deploy-lightrag`
* files it reads/writes
* whether it calls Docker
* whether it calls the backend
* whether it needs login
* human output shape
* JSON output shape
* error cases
* tests to add

### 5. File/Module Design

Propose a minimal module structure.

Example target:

```text
cli/
  main.py                  # Typer root only; wires command groups
  api_client.py            # existing backend HTTP client
  credentials.py           # existing credential store
  output.py                # shared human/json output helpers
  errors.py                # shared CLI error helpers
  commands/
    auth.py
    documents.py
    admin_documents.py
    jobs.py
    planned.py
    lightrag_domains.py
  lightrag/
    paths.py
    manifest.py
    compose.py
    docker.py
    health.py
```

Do not over-engineer. If fewer files are better, explain why.

### 6. Deployment Asset Plan

Decide where LightRAG deployment assets should live inside `context_engine`.

Consider:

```text
external/lightrag/
  docker-compose.domains.yml
  Dockerfile.lightrag-local
  data/
    domains.json
    domains/
    config/
```

or:

```text
.data/lightrag/
```

or another lean alternative.

Explain the tradeoff and recommend one.

### 7. Migration/Copy Strategy

Create a source-to-target migration table:

| easy-deploy-lightrag source             | context_engine target                    | action | notes                    |
| --------------------------------------- | ---------------------------------------- | ------ | ------------------------ |
| `cli/main.py` domain functions          | `cli/lightrag/...`                       | adapt  | split into small helpers |
| `scripts/deploy_wizard.sh`              | `scripts/deploy-lightrag.sh`             | adapt  | call `ragcli lightrag`   |
| `docker-compose.domains.yml` generation | `cli/lightrag/compose.py`                | adapt  | keep deterministic       |
| env generation                          | `cli/lightrag/manifest.py` or `paths.py` | adapt  | never print secrets      |

### 8. Testing Plan

Produce a TDD plan with slices.

Required test areas:

* existing CLI commands still pass
* `ragcli lightrag domain add` writes manifest and env files
* duplicate domain is rejected
* invalid domain name is rejected
* unavailable port behavior is deterministic
* `domain list --output json` is stable
* `domain remove` archives domain folder before removal
* Docker commands are mocked
* health checks are mocked
* no secrets are printed
* local LightRAG commands do not require backend login
* backend API commands still require login where appropriate

### 9. Risk Review

Identify architectural risks:

* one huge CLI file
* leaking secrets from env files
* requiring Docker in unit tests
* confusing backend admin auth with local operator commands
* coupling `context_engine` to LightRAG internals
* breaking stable JSON output
* duplicating easy-deploy code without simplification
* Windows path/script compatibility
* stale domain manifest vs actual running Docker containers

For each risk, propose mitigation.

### 10. Final Deliverable

Return a markdown implementation plan with these sections:

1. Executive summary
2. Current-state map
3. Recommended command surface
4. Architecture/module design
5. Source-to-target migration table
6. Behavior and output contracts
7. TDD implementation phases
8. Risks and mitigations
9. Explicit deferrals
10. Next command to give the coding agent for Phase 1

---

## Important Judgment Calls To Make

Be opinionated. Recommend the leanest design.

Specifically answer:

1. Should LightRAG deployment commands live under `ragcli lightrag ...`?
2. Should they require backend login?
3. Should deployment logic call backend routes or remain local?
4. Should `deploy_wizard.sh` be copied as-is, wrapped, or replaced?
5. Should the existing `context_engine` CLI be split into modules before adding LightRAG?
6. What is the smallest safe Phase 1?
7. What should be deferred?

---

## Output Style

Write for a junior developer who will implement the plan.

Use clear file paths, command examples, and acceptance criteria.

Do not write code yet.

Do not make unsupported assumptions. If a backend route does not exist, mark it as a backend gap. If a capability is local-only, mark it as local operator behavior.

```

My architectural bias: the new surface should be **`ragcli lightrag ...`**, and those commands should be local operator commands, not authenticated backend API commands, unless they call `context_engine` routes. The existing docs already distinguish supported backend commands from backend gaps, and the current LightRAG plan says the deployment wrapper should stay thin and remote behavior should be controlled by `LIGHTRAG_ENABLED`. :contentReference[oaicite:3]{index=3} :contentReference[oaicite:4]{index=4}
::contentReference[oaicite:5]{index=5}
```
