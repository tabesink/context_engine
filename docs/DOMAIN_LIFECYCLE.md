# Domain Lifecycle

Domains represent LightRAG runtime/workspace identity. They are the unit an admin creates and operates, and the unit users select for upload, retrieval, and graph browsing.

## Allowed Lifecycle Actions

The normal lifecycle is intentionally small:

- create
- start
- stop
- delete

UI surfaces should not expose repair, recreate, regenerate, purge, upload document, view documents, or view logs as normal domain card actions. Document workflows belong on document surfaces, and runtime diagnostics should be deliberate debug/admin views.

## State Ownership

- The `lightrag_domains` database row stores desired state and admin-visible metadata such as ID, display name, health summary, and embedding snapshot metadata.
- Docker, HTTP health checks, and remote LightRAG probes provide observed runtime state.
- Generated manifest, compose, and `domain.env` files are deployment artifacts.
- Operations record lifecycle transitions and current/final status.
- Audit logs record who initiated lifecycle actions.

In short: DB row = desired state; Docker/HTTP = observed runtime state; generated files = artifacts; operations/audit = history and visibility.

## Create

Create registers a managed domain and writes deployment metadata. It should validate provider and embedding configuration before creating a domain that cannot later ingest. The selected embedding configuration is locked into the domain snapshot.

Create should produce a domain operation and audit entry.

## Start

Start refreshes generated runtime artifacts, provisions storage as needed, invokes the Docker runner boundary, and records observed health. A successful start should update the domain runtime summary and mark the corresponding operation succeeded.

## Stop

Stop shuts down the managed runtime through the deployment service boundary. It should preserve uploaded documents, parsed structure, domain metadata, and generated files unless the deployment service intentionally refreshes artifacts.

## Delete

Delete removes or disables the active managed domain according to the deployment service behavior. Current behavior archives runtime files and marks the domain unavailable while preserving local document records.

Delete is destructive from the runtime perspective, so it should remain explicit in the UI and continue writing operation and audit records.
