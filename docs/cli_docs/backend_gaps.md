# Backend Gaps

These capabilities are intentionally not exposed as successful CLI/TUI actions until the backend owns a real route and behavior contract. The TUI must not fake success for them.

| Capability | Current route | Suggested route | Priority | Note |
|---|---|---|---|---|
| interactive chat | none | `POST /chat` or `POST /messages` | later | Build backend conversation/message semantics first. |
| user listing | none | `GET /users` | later | Requires admin user-management API scope. |
| conversation history | none | `GET /conversations` | later | Requires persisted conversation model. |
| conversation messages | none | `GET /messages` | later | Requires persisted message model. |
| agent run status | none | `GET /runs/{run_id}` | later | Requires run/job model separate from indexing jobs. |
| human approval queue | none | `GET /runs/approvals` | later | Requires approval workflow. |
| corpus version publish | none | `POST /admin/corpus/publish` | later | Requires corpus versioning contract. |
| corpus version rollback | none | `POST /admin/corpus/rollback` | later | Requires corpus versioning contract. |
| corpus cleanup | none | `POST /admin/corpus/cleanup` | later | Requires retention and deletion policy. |

Implementation path: add the backend route and tests first, add a `cli/services/` wrapper second, then expose the capability in the TUI.
