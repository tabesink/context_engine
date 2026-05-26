---
name: centralize-runtime-ports
overview: Centralize server/client port configuration in root .env and remove hardcoded dev-port drift between scripts and frontend defaults.
todos:
  - id: add-client-port-env
    content: Add CLIENT_PORT to root env example and document intended defaults.
    status: completed
  - id: wire-deploy-all-env-ports
    content: Make deploy-all parse API_PORT and CLIENT_PORT from root .env and pass them to npm dev environment.
    status: completed
  - id: remove-hardcoded-client-dev-port
    content: Update client/package.json dev script to stop pinning -p 3007 and rely on PORT env.
    status: completed
  - id: align-client-api-fallback
    content: Update client API fallback port default and add README note about single-source port configuration.
    status: completed
  - id: validate-end-to-end
    content: Run shell syntax/startup checks and verify login flow works with env-defined ports.
    status: completed
  - id: unify-cli-api-default
    content: Align deploy-cli defaults with API_PORT from root .env and remove stale 8000 fallback drift.
    status: completed
  - id: standardize-client-api-env-name
    content: Choose one canonical NEXT_PUBLIC API base env variable and keep backward-compatible alias handling.
    status: completed
  - id: centralize-host-bindings
    content: Introduce optional host envs (API_HOST, CLIENT_HOST, LIGHTRAG_HOST) for non-localhost setups and wire scripts/services.
    status: completed
  - id: align-powershell-parity
    content: Mirror centralized env-driven behavior in deploy-server.ps1 and deploy-cli.ps1 to avoid shell-specific drift.
    status: completed
  - id: optional-lightrag-port-centralization
    content: Make frontend LightRAG default port resolve from env/config fallback instead of hardcoded constant when practical.
    status: completed
isProject: false
---

# Centralize Runtime Ports In Root Env

## Goal
Use root `.env` as the single source of truth for local runtime ports so server, client, and API base resolution stay aligned.

## Changes
### Phase 1 (lean, immediate)
- Update [`/data/home/tkodippili/Desktop/localTest_context_engine/.env.example`](/data/home/tkodippili/Desktop/localTest_context_engine/.env.example) to define both:
  - `API_PORT` (already present)
  - `CLIENT_PORT` (new; default `3007`)
- Update [`/data/home/tkodippili/Desktop/localTest_context_engine/scripts/deploy-all.sh`](/data/home/tkodippili/Desktop/localTest_context_engine/scripts/deploy-all.sh):
  - Parse `API_PORT` and `CLIENT_PORT` from root `.env`.
  - Start frontend with `PORT=$CLIENT_PORT` and `NEXT_PUBLIC_API_PORT=$API_PORT`.
  - Keep current passthrough args for `deploy-server.sh` unchanged.
- Update [`/data/home/tkodippili/Desktop/localTest_context_engine/client/package.json`](/data/home/tkodippili/Desktop/localTest_context_engine/client/package.json):
  - Change `dev` script from hardcoded `next dev -H 127.0.0.1 -p 3007` to env-driven `next dev -H 127.0.0.1`.
- Update [`/data/home/tkodippili/Desktop/localTest_context_engine/client/src/lib/api/client.ts`](/data/home/tkodippili/Desktop/localTest_context_engine/client/src/lib/api/client.ts):
  - Replace `DEFAULT_API_PORT = "8088"` with `"8010"` to match local defaults when env injection is absent.
- Update [`/data/home/tkodippili/Desktop/localTest_context_engine/README.md`](/data/home/tkodippili/Desktop/localTest_context_engine/README.md) with a short “Port configuration” note stating root `.env` controls local ports.

### Phase 2 (additional centralization requested)
- Update [`/data/home/tkodippili/Desktop/localTest_context_engine/scripts/deploy-cli.sh`](/data/home/tkodippili/Desktop/localTest_context_engine/scripts/deploy-cli.sh) and [`/data/home/tkodippili/Desktop/localTest_context_engine/scripts/deploy-cli.ps1`](/data/home/tkodippili/Desktop/localTest_context_engine/scripts/deploy-cli.ps1):
  - Remove stale `8000` fallback drift.
  - Resolve API base from root `.env` `API_PORT` consistently unless explicit override is provided.
- Standardize client API env naming in [`/data/home/tkodippili/Desktop/localTest_context_engine/client/src/lib/api/client.ts`](/data/home/tkodippili/Desktop/localTest_context_engine/client/src/lib/api/client.ts):
  - Choose one canonical key (`NEXT_PUBLIC_API_URL` or `NEXT_PUBLIC_BACKEND_BASE_URL`).
  - Keep compatibility for the alias during transition.
- Add optional host centralization (`API_HOST`, `CLIENT_HOST`, `LIGHTRAG_HOST`) and wire where currently hardcoded to `127.0.0.1`:
  - [`/data/home/tkodippili/Desktop/localTest_context_engine/scripts/deploy-all.sh`](/data/home/tkodippili/Desktop/localTest_context_engine/scripts/deploy-all.sh)
  - [`/data/home/tkodippili/Desktop/localTest_context_engine/scripts/deploy-server.sh`](/data/home/tkodippili/Desktop/localTest_context_engine/scripts/deploy-server.sh)
  - [`/data/home/tkodippili/Desktop/localTest_context_engine/app/lightrag_deploy/service.py`](/data/home/tkodippili/Desktop/localTest_context_engine/app/lightrag_deploy/service.py) (if host binding should be configurable there too)
- Ensure PowerShell parity for centralized behavior:
  - [`/data/home/tkodippili/Desktop/localTest_context_engine/scripts/deploy-server.ps1`](/data/home/tkodippili/Desktop/localTest_context_engine/scripts/deploy-server.ps1)
- Optional: centralize frontend LightRAG default port currently hardcoded in [`/data/home/tkodippili/Desktop/localTest_context_engine/client/src/stores/lightrag-domain-store.ts`](/data/home/tkodippili/Desktop/localTest_context_engine/client/src/stores/lightrag-domain-store.ts) (`9621`) if you want full env-driven consistency.

## Validation
- Run `bash -n scripts/deploy-all.sh`.
- Run `bash -n scripts/deploy-server.sh` and shell-check updated CLI scripts.
- Launch `bash scripts/deploy-all.sh` and verify startup log prints selected API/client ports.
- Verify frontend login (`admin/admin123`) succeeds without manual exports.
- Optional sanity check: change `API_PORT` and `CLIENT_PORT` in `.env`, rerun, and confirm both services honor new values.
- Verify CLI still connects correctly with default config (`scripts/deploy-cli.sh`) and with explicit `--api-base-url`.