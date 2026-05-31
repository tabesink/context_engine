# Domain Surface: Do Not Expose Upload Workflow

The domain lifecycle surface should stay lean.

## Allowed lifecycle actions

```text
Create
Start
Stop
Delete
```

## Remove from domain card/menu

```text
Upload Documents
View Documents
View Logs
Repair
Recreate
Regenerate
Purge
Manual Refresh Status
```

## Rationale

Documents belong on the Documents surface.
Domain runtime belongs on the Domain lifecycle surface.
Jobs/operations/logs belong on Observability/Admin diagnostics.

This keeps the app low-entropy and prevents every surface from becoming an admin console.
