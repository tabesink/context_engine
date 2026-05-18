# 4. Terminal UI Integration Plan

## 4.1 Current CLI/TUI Architecture Assumption

Do not design for the older `ragcli` command-tree model.

Use the current terminal UI structure:

```text
cli/
  launcher.py              # terminal UI launcher
  config.py                # optional argparse/settings
  credentials.py           # credential storage
  api_client.py            # HTTP wrapper
  services/                # feature-oriented API call helpers
  tui/                     # Rich TUI screens
  main.py                  # legacy compatibility delegate only
```

## 4.2 TUI Rules

- TUI screens are presentation only.
- TUI screens call `cli/services/*`.
- `cli/services/*` calls Context Engine API through `ApiClient`.
- No Docker calls in TUI screens.
- No direct LightRAG calls in TUI screens.
- No file/env/manifest manipulation in TUI screens.
- `cli/main.py` remains a compatibility delegate to launcher only.

## 4.3 New CLI Service

Add:

```text
cli/services/lightrag_domains.py
```

Suggested class:

```python
class LightRAGDomainService:
    def __init__(self, api_client: ApiClient): ...

    def list_user_domains(self) -> dict: ...
    def list_admin_domains(self) -> dict: ...
    def create_domain(self, payload: dict) -> dict: ...
    def show_domain(self, domain_id: str) -> dict: ...
    def up_domain(self, domain_id: str) -> dict: ...
    def down_domain(self, domain_id: str) -> dict: ...
    def recreate_domain(self, domain_id: str) -> dict: ...
    def regenerate_domain(self, domain_id: str | None = None) -> dict: ...
    def remove_domain(self, domain_id: str, *, permanent: bool = False) -> dict: ...
```

This class only constructs HTTP requests to Context Engine.

## 4.4 Admin TUI Menu

Add a screen flow like:

```text
Admin Menu
  ├── Documents
  ├── Jobs
  ├── Logs
  ├── System Status
  └── LightRAG Domains
        ├── List domains
        ├── Create domain
        ├── Show domain detail
        ├── Start domain
        ├── Stop domain
        ├── Recreate domain
        ├── Regenerate config
        ├── Archive/remove domain
        └── Health/status
```

## 4.5 Normal User Domain Selection

Normal users should be able to select a LightRAG domain for query/upload contexts where applicable.

Suggested user-safe UI:

```text
Query Settings
  ├── Retrieval mode: auto / semantic / navigation / hybrid
  ├── LightRAG domain: [default / fatigue / abaqus / hospital-beds]
  └── Top K: 8
```

The user-facing domain selector must call:

```text
GET /lightrag/domains
```

not the admin endpoint.

## 4.6 Admin Domain List Screen

Example layout:

```text
┌──────────────────────────────────────────────────────────────┐
│ LightRAG Domains                                             │
├─────────────┬────────────┬─────────┬──────────┬──────────────┤
│ Domain      │ Port       │ Status  │ Health   │ Last Updated │
├─────────────┼────────────┼─────────┼──────────┼──────────────┤
│ fatigue     │ 9622       │ running │ healthy  │ 2026-05-18   │
│ abaqus      │ 9623       │ stopped │ unknown  │ 2026-05-18   │
└─────────────┴────────────┴─────────┴──────────┴──────────────┘

Actions: [C]reate  [S]tart  S[t]op  [R]ecreate  [D]etail  [A]rchive  [B]ack
```

## 4.7 Create Domain Screen

Fields:

```text
Domain ID:       fatigue
Display name:    Fatigue Manuals
Host port:       blank for auto
Make default:    no
```

Validation should happen both in TUI and backend, but backend is source of truth.

## 4.8 Remove Domain Screen

Default behavior:

```text
Archive domain data? yes
Permanent delete? no
```

Permanent delete should require a deliberate confirmation phrase, for example:

```text
Type DELETE fatigue to permanently delete this domain.
```

But permanent delete should only be available if:

```env
LIGHTRAG_ALLOW_PERMANENT_DELETE=true
```

## 4.9 Error Display

Map backend errors to clear TUI messages:

| Backend Error | TUI Message |
|---|---|
| Deployment disabled | `LightRAG deployment is disabled. Enable LIGHTRAG_DEPLOY_ENABLED=true.` |
| Docker unavailable | `Docker is not reachable from Context Engine.` |
| Port conflict | `Port 9622 is already used by another domain or process.` |
| Invalid domain ID | `Use lowercase letters, numbers, hyphen, or underscore.` |
| Domain not found | `Domain does not exist.` |
| Permission denied | `Admin access required.` |

## 4.10 Testing TUI

Add tests around:

- service URL/payload construction
- admin screen rendering with fake API response
- user domain selector rendering
- create-domain form validation
- remove-domain confirmation behavior
- error rendering

Do not test real Docker from TUI tests.
