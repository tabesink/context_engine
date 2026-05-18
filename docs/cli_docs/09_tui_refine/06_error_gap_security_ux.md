# 6. Error, Backend Gap, and Security UX

## 6.1 Standard Error Panel

```text
ERROR

code:    forbidden
message: Admin access required
route:   POST /admin/documents/upload
status:  403
time:    31 ms

Next:
- Sign in as an admin.
- Check current role with /auth/me.
```

## 6.2 Error Panel Must Include

- backend error code
- backend message
- method and route
- HTTP status
- latency if available
- practical next action

## 6.3 Error Panel Must Not Include

- access token
- password
- raw request headers
- API keys
- stack traces by default
- local filesystem secrets
- Docker secrets
- LightRAG API key

## 6.4 Connection Error

```text
ERROR

code:    connection_failed
message: Could not connect to backend
route:   GET /auth/me
backend: http://127.0.0.1:8010

Next:
- Start the backend.
- Check --api-base-url.
- Confirm saved session backend URL.
```

## 6.5 Auth Error

```text
ERROR

code:    auth_required
message: Sign in via context-engine first
route:   GET /documents
status:  401

Next:
- Go to Login.
```

## 6.6 Forbidden Error

```text
ERROR

code:    forbidden
message: Admin access required
route:   GET /admin/documents
status:  403

Next:
- Check current role in session summary.
- Sign in as an admin.
```

## 6.7 Backend Gap Panel

```text
BACKEND GAP

Capability: Document text search
Current route: none
Suggested route: GET /documents/search?q=
Status: not_supported_by_backend

Next:
- Implement backend route first.
- Add cli/services wrapper.
- Add TUI screen.
- Add tests.
```

## 6.8 Sensitive Output Rules

- Never print bearer tokens.
- Never print passwords.
- Never print API keys.
- Never display raw request headers unless sanitized.
- Display file upload path only when useful; avoid leaking unnecessary absolute paths by default.
- For LightRAG domain screens, do not display secrets from generated env files.
- For Docker errors, show stderr summary but scrub secrets.

## 6.9 Raw JSON Redaction

Before rendering raw JSON:

- redact fields named `token`, `access_token`, `password`, `api_key`, `secret`, `authorization`
- truncate huge `content`, `full_text`, `embedding`, and raw graph arrays by default
- include a note when fields are truncated or redacted

Example:

```json
{
  "access_token": "[REDACTED]",
  "content": "[TRUNCATED 12450 chars]"
}
```
