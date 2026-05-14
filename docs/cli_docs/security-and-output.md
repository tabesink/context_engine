# Security And Output

## Credential Storage

The CLI stores only:

- backend base URL
- access token

It never stores passwords. `CredentialStore` prefers OS keyring. If keyring is unavailable or disabled, it falls back to a local credentials file and prints a warning naming that file. The fallback file is written with restricted permissions when the platform supports it.

Protected commands use the saved base URL from the login session. If a command is run with a different root `--api-base-url`, the CLI prints this warning to stderr and continues with the saved session:

```text
warning: saved session uses a different --api-base-url; re-run login to switch
```

## Sensitive Output Rules

- Never print access tokens.
- Never print passwords.
- Do not echo request headers in errors.
- Preserve backend error messages, but avoid adding sensitive local details.
- Connection failures should include a practical hint to start the backend or pass `--api-base-url`.

## JSON Error Shape

JSON failures use this shape:

```json
{
  "error": {
    "code": "auth_required",
    "message": "Run `ragcli login` first.",
    "status": 1
  }
}
```

Backend errors preserve backend-provided `code`, `message`, and HTTP status when available.

## Human Error Shape

Human failures are short and actionable. They are rendered with Rich color in the terminal, but the text content is:

```text
auth_required: Run `ragcli login` first.
```

For unsupported planned commands:

```text
not_supported_by_backend: `COMMAND` needs a backend route first. See docs/cli_docs/api-contract.md.
```

## Admin Boundary

The CLI does not infer admin permissions locally. It sends the request with the stored token and renders the backend response. The backend owns authorization through `require_admin`.

## LightRAG Boundary

The CLI never stores LightRAG credentials and never calls LightRAG directly. LightRAG graph commands call the Context Engine backend. The backend decides whether LightRAG is enabled and how to authenticate to the remote service.

## Output Contract

Human output can change for readability. JSON output is the stable contract and should be covered by behavior tests for every supported command. Many current human responses are pretty-printed JSON or simple tables, so scripts should always use `--output json`.
