---
name: ragcli-tui-ux-fix-plan
overview: Implement the full 9-slice TDD UX fix for Documents upload flow in `ragcli ui`, reusing the existing upload API contract and current TUI architecture.
todos:
  - id: slice-1-empty-state
    content: Add failing/passing tests and implementation for empty documents actionable menu, no duplicate empty text, and hidden Enter Open when no docs.
    status: completed
  - id: slice-2-form-navigation
    content: Implement upload form navigation from Documents and editable file-path input behavior with corresponding tests.
    status: completed
  - id: slice-3-local-validation
    content: Add local file existence validation path and upload error screen behavior with no backend-call test coverage.
    status: completed
  - id: slice-4-upload-contract
    content: Wire valid form submission to existing ApiClient.post_file contract for /admin/documents/upload and verify multipart semantics in tests.
    status: completed
  - id: slice-5-job-success
    content: Implement upload success screen when job_id exists, including View job status action and tests.
    status: completed
  - id: slice-6-forwarded-success
    content: Implement LightRAG-forwarded success handling when job_id is null, with action gating and tests.
    status: completed
  - id: slice-7-forbidden
    content: Add forbidden-screen behavior for backend 403 responses from upload flow and test it.
    status: completed
  - id: slice-8-upload-shortcut
    content: Add U shortcut on non-empty documents screen while preserving enter-to-open behavior, backed by tests.
    status: completed
  - id: slice-9-screen-clearing
    content: Ensure render transitions replace prior screen content in TUI path and add regression test for stale output.
    status: completed
  - id: final-verify
    content: Run target tests/lints for touched files and summarize outcomes plus any follow-up fixes.
    status: completed
isProject: false
---

# RAGCLI TUI Upload UX Fix Implementation Plan

## Scope and Outcome
Implement all 9 slices from `ui_ux_fix.md` against the active TUI stack so users can upload documents end-to-end inside `ragcli ui` (empty-state actions, upload form, success/error/forbidden handling, and screen-clearing behavior), with test-first vertical slices.

## Source of Truth
- Brainstorm/spec: [d:/Projects/context_engine/docs/cli_docs/05_ragcli_tui_ux_fix/ui_ux_fix.md](d:/Projects/context_engine/docs/cli_docs/05_ragcli_tui_ux_fix/ui_ux_fix.md)
- TDD method: [d:/Projects/context_engine/.cursor/skills/engineering/tdd/SKILL.md](d:/Projects/context_engine/.cursor/skills/engineering/tdd/SKILL.md)

## Implementation Targets
- TUI behavior and navigation: [d:/Projects/context_engine/cli/tui/screens/content.py](d:/Projects/context_engine/cli/tui/screens/content.py), [d:/Projects/context_engine/cli/tui/navigation.py](d:/Projects/context_engine/cli/tui/navigation.py), [d:/Projects/context_engine/cli/tui/keys.py](d:/Projects/context_engine/cli/tui/keys.py)
- Existing screen builders to reuse/adapt: [d:/Projects/context_engine/cli/screens/documents.py](d:/Projects/context_engine/cli/screens/documents.py), [d:/Projects/context_engine/cli/screens/admin_documents.py](d:/Projects/context_engine/cli/screens/admin_documents.py)
- API contract reuse: [d:/Projects/context_engine/cli/api_client.py](d:/Projects/context_engine/cli/api_client.py), [d:/Projects/context_engine/cli/flows/upload_document.py](d:/Projects/context_engine/cli/flows/upload_document.py)
- TUI regression and new behavior tests: [d:/Projects/context_engine/tests/test_cli_tui.py](d:/Projects/context_engine/tests/test_cli_tui.py)

## Execution Strategy (TDD Vertical Slices)
For each slice: write one failing test -> implement minimum code to pass -> run focused tests -> refactor safely.

1. Empty docs screen menu (Upload/Refresh/Back/Quit), hide `Enter Open`, remove duplicate empty text.
2. Selecting `Upload document` opens upload form screen with editable file path.
3. Invalid local path shows upload error screen and skips backend call.
4. Valid path submits multipart `POST /admin/documents/upload` via existing client contract.
5. Success with `job_id` shows completion state with `View job status` option.
6. Success without `job_id` handles LightRAG-forwarded case without crash and with correct actions.
7. Backend `403` renders explicit forbidden screen from upload flow.
8. Non-empty documents screen adds `U` shortcut while preserving open-detail behavior.
9. Ensure render loop clears/replaces content between screen transitions (no stale appended output in TUI test path).

## Data and Control Flow
```mermaid
flowchart TD
  documentsScreen[DocumentsScreen] -->|"Enter Upload or U"| uploadForm[UploadDocumentScreen]
  uploadForm -->|Validate local path| localValidation[PathExistsCheck]
  localValidation -->|invalid| uploadError[UploadErrorScreen]
  localValidation -->|valid| apiUpload[ApiClient.post_file /admin/documents/upload]
  apiUpload -->|403| forbiddenScreen[ForbiddenScreen]
  apiUpload -->|200 job_id present| uploadSuccessJob[UploadCompleteWithJob]
  apiUpload -->|200 job_id null| uploadSuccessForwarded[UploadCompleteForwarded]
  uploadSuccessJob --> jobsScreen[JobStatusScreen]
  uploadSuccessJob --> documentsRefresh[DocumentsScreen refresh]
  uploadSuccessForwarded --> documentsRefresh
```

## Design Constraints to Enforce
- Keep authorization decisions backend-driven (no local admin inference).
- Reuse existing upload endpoint contract and multipart field (`file`).
- Keep rendering ASCII/simple monochrome and avoid leaking secrets.
- Preserve existing navigation keys (`B`, `Q`, `Ctrl+R`) while adding `U` for upload shortcut.

## Verification Plan
- Add/extend focused tests in `tests/test_cli_tui.py` for all 9 slices.
- Run targeted test module first, then broader CLI tests if needed for regressions.
- Validate no new lint issues in touched files.
- Manually sanity-check navigation transitions in `ragcli ui` if test harness cannot fully emulate terminal redraw behavior.

## Risks and Mitigations
- Existing shared screen builders may still emit CLI-style command hints; mitigate by handling TUI-specific empty-state rendering in `DocumentsScreen` where needed.
- LightRAG metadata shape may differ from previous assumptions; mitigate by reading nested `document.metadata.lightrag` defensively.
- Existing dirty working tree can mask regressions; mitigate by only touching scoped files and validating tests around modified behavior.