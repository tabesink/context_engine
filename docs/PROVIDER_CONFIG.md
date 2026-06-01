# Provider Configuration

Context Engine uses a hybrid provider configuration model.

## Source Of Truth

- DB-backed AI model profiles and encrypted provider secrets are the admin-managed source for runtime provider configuration.
- Environment variables bootstrap defaults and provide fallback secret values.
- Generated `domain.env` files are deployment snapshots written for LightRAG domains.

This means the Settings UI may create profiles, set defaults, test profiles, and manage write-only secrets. It should not imply that editing a generated `domain.env` file is the normal way to configure providers.

## Domain Snapshots

When an admin creates a managed LightRAG domain, the selected embedding profile is copied into the domain manifest as an embedding snapshot. That snapshot captures the provider, binding, base URL, model, dimensions, token limit, and fingerprint used by the domain.

The generated `domain.env` receives provider runtime values from the active profile and secret resolver. LightRAG consumes those values, while Context Engine keeps the editable configuration in DB-backed settings.

## Secret Boundary

- Provider secrets may be stored encrypted in the database.
- If a secret is missing from encrypted storage, the resolver may read the matching environment variable.
- Secrets are emitted only to generated per-domain `domain.env` files.
- Secrets must not be written into compose output, manifest JSON, frontend API responses, or audit metadata.

## Operational Rule

Changing a provider profile or default affects future resolution. Existing domain embedding snapshots stay fixed unless an explicit domain migration flow is built.

