# Security And Output

## Credential Storage

The terminal client stores only:

- backend base URL
- access token

It never stores passwords. `CredentialStore` prefers OS keyring unless `--no-keyring` forces file storage. When keyring is unavailable or disabled, it falls back to a local credentials file and prints a warning naming that file. The fallback file is written with restricted permissions when the platform supports it.

After sign-in, navigation uses the saved base URL. If the launcher is started with a different `--api-base-url`, the session flow surfaces a warning and continues using the stored URL until the user signs out or signs in again.

## Sensitive Output Rules

- Never print access tokens.
- Never print passwords.
- Do not echo raw request headers in errors.
- Preserve backend error messages, but avoid adding sensitive local details.
- Connection failures should include a practical hint to start the backend or pass `--api-base-url`.

## JSON Error Shape (automation / tests)

JSON failures use this shape when the client wraps them:

```json
{
  "error": {
    "code": "auth_required",
    "message": "Sign in via `context-engine` first.",
    "status": 1
  }
}
```

Backend errors preserve backend-provided `code`, `message`, and HTTP status when available.

## Human-facing error copy

Human failures are short and actionable. They are rendered with Rich color in the terminal, but the text content is:

```text
auth_required: Sign in via `context-engine` first.
```

For unsupported planned backend areas:

```text
not_supported_by_backend: `FEATURE` needs a backend route first. See docs/cli_docs/api-contract.md.
```

## Admin Boundary

The client does not infer admin permissions locally. It sends the stored token and renders the backend response. Authorization is enforced server-side via `require_admin`.

## LightRAG Boundary

The client never stores LightRAG credentials and never calls LightRAG directly. LightRAG graph screens call the Context Engine backend. The backend decides whether LightRAG is enabled and how to authenticate to the remote service.

## Output contract

Rich tables and summaries are **best-effort** operator views. For stable automation, call HTTP handlers directly and parse JSON—do not rely on formatted terminal output as a script contract.
