# ragcli TUI Visual Screen Targets

This bundle contains downloadable markdown documentation for improving the `ragcli ui` visual UX.

Focus:
- clean full-screen TUI views
- no stale deploy/startup banner inside active TUI screens
- semantic color usage
- ASCII tables
- compact action footers
- useful default selections
- upload-result screens that guide the user to the next step
- screen examples the coding agent can implement against

## Files

1. `01_VISUAL_UX_PRINCIPLES.md`
2. `02_UPLOAD_FLOW_SCREEN_TARGETS.md`
3. `03_DOCUMENTS_AND_RETRIEVAL_SCREEN_TARGETS.md`
4. `04_ADMIN_JOBS_LIGHTRAG_ERROR_SCREEN_TARGETS.md`
5. `05_CODING_AGENT_VISUAL_IMPLEMENTATION_PROMPT.md`

## Key rule

The TUI must behave like a screen application:

```text
clear -> render active screen -> read key -> update state -> clear -> render next screen
```

Do not append new TUI output under old terminal output.

## Color policy

Use mostly black-and-white text.

Color should be reserved for:
- success
- warning
- error
- selected row/action
- disabled/backend-gap states
- subtle API group accent

Use ASCII tables only.
