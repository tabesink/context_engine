# 4. LightRAG Domains Screen Plan

## 4.1 Goal

Move all LightRAG domain deployment CRUD out of the root menu and into the `LightRAG Domains` screen.

Root menu should contain only:

```text
LightRAG Domains
```

not:

```text
LightRAG Domains
Create LightRAG Domain
Start LightRAG Domain
Stop LightRAG Domain
Recreate LightRAG Domain
Remove LightRAG Domain
```

## 4.2 Backend Contract

Use existing domain lifecycle routes:

| UI action | Backend route |
|---|---|
| Retrieval domain picker | `GET /lightrag/domains` |
| List configured domains | `GET /admin/lightrag/domains` |
| Create domain | `POST /admin/lightrag/domains` |
| Show domain detail | `GET /admin/lightrag/domains/{domain_id}` |
| Start domain | `POST /admin/lightrag/domains/{domain_id}/up` |
| Stop domain | `POST /admin/lightrag/domains/{domain_id}/down` |
| Recreate domain | `POST /admin/lightrag/domains/{domain_id}/recreate` |
| Regenerate domain files | `POST /admin/lightrag/domains/{domain_id}/regenerate` |
| Archive remove | `DELETE /admin/lightrag/domains/{domain_id}` |
| Permanent delete | `DELETE /admin/lightrag/domains/{domain_id}?permanent=true` |

## 4.3 Screen Layout

```text
LIGHTRAG DOMAINS

Configured domains:

+----------+--------------+------+----------+----------+----------------+
| Domain   | Display Name | Port | Runtime  | Health   | Default        |
+----------+--------------+------+----------+----------+----------------+
| fatigue  | Fatigue Docs | 9622 | running  | healthy  | yes            |
| abaqus   | Abaqus Docs  | 9623 | stopped  | unknown  | no             |
+----------+--------------+------+----------+----------+----------------+

Actions:
> Create Domain
  Show Domain Detail
  Start Domain
  Stop Domain
  Recreate Domain
  Regenerate Domain Files
  Archive Remove Domain
  Permanent Delete Domain
  Back
```

## 4.4 Create Domain Form

```text
CREATE LIGHTRAG DOMAIN

Domain ID:       fatigue
Display name:    Fatigue Manuals
Host port:       9622  (blank = auto)
Make default:    yes/no

Submit / Cancel
```

Request body:

```json
{
  "domain_id": "fatigue",
  "display_name": "Fatigue Manuals",
  "host_port": 9622,
  "make_default": true
}
```

## 4.5 Start / Stop / Recreate

These flows should use a select-domain first pattern:

```text
START LIGHTRAG DOMAIN

Select domain:
> fatigue    stopped    port 9622
  abaqus     running    port 9623

Confirm start selected domain? yes/no
```

## 4.6 Remove Domain

Default is archive:

```text
ARCHIVE REMOVE LIGHTRAG DOMAIN

Domain: fatigue

This will:
- stop the domain container if running
- remove it from active domain manifest
- move .data/lightrag/domains/fatigue to .data/lightrag/deleted/fatigue-<timestamp>

Type ARCHIVE fatigue to continue:
```

Permanent delete:

```text
PERMANENT DELETE LIGHTRAG DOMAIN

Domain: fatigue

This permanently deletes domain data.
This is only allowed when LIGHTRAG_ALLOW_PERMANENT_DELETE=true.

Type DELETE fatigue to continue:
```

## 4.7 Service Layer

Add or update:

```text
cli/services/lightrag_domains.py
```

This file should call backend routes through `ApiClient`.

It must not:

- call Docker
- edit `.data`
- generate env files
- call LightRAG directly

## 4.8 TUI Screen Files

Likely files:

```text
cli/tui/screens/lightrag_domains.py
cli/tui/renderers/lightrag_domains.py
```

or equivalent names matching current project structure.

## 4.9 Tests

Add/update tests:

```text
tests/test_cli_tui.py
tests/test_cli_services.py
tests/test_cli_screen_renderers.py
```

Required assertions:

- Root menu includes only one `LightRAG Domains` item.
- Root menu does not include Create/Start/Stop/Recreate/Remove LightRAG Domain.
- LightRAG Domains screen contains create/start/stop/recreate/remove actions.
- TUI service methods call the correct admin routes.
- Permanent delete requires typed confirmation.
