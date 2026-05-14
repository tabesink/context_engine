# Security And Output

## Credential Storage

The CLI stores only:

- backend base URL
- access token

It never stores passwords. The credential store should prefer OS keyring. If keyring is unavailable, it may fall back to a local credentials file and must print a warning naming that file.

## Sensitive Output Rules

- Never print access tokens.
- Never print passwords.
- Do not echo request headers in errors.
- Preserve backend error messages, but avoid adding sensitive local details.
- Connection failures should include the target base URL and a practical hint.

## JSON Error Shape

JSON failures should use this shape:

```json
{
  "error": {
    "code": "auth_required",
    "message": "Run `ragcli login` first.",
    "status": 1
  }
}
```

Backend errors should preserve backend-provided `code`, `message`, and HTTP status when available.

## Human Error Shape

Human failures should be short and actionable:

```text
auth_required: Run `ragcli login` first.
```

For unsupported planned commands:

```text
not_supported_by_backend: this command needs a backend route first. See docs/cli_docs/api-contract.md.
```

## Admin Boundary

The CLI should not try to infer admin permissions locally. It should send the request with the stored token and render the backend response. The backend owns authorization through `require_admin`.

## Output Contract

Human output can change for readability. JSON output is the stable contract and should be covered by behavior tests for every supported command.
