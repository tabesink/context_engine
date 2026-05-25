# Post-Implementation Review Prompt

You are a senior software architect reviewing a PR in `context_engine`.

The PR is supposed to add support for displaying retrieved evidence in the WebUI right-hand side panel.

## Review Goals

Verify that the PR:

1. Adds a clean evidence-only retrieval endpoint.
2. Reuses the existing retrieval service.
3. Does not duplicate query/retrieval/auth logic.
4. Keeps removed `/query/*` routes removed unless the PR explicitly proposes an API compatibility decision.
5. Provides a stable response contract for WebUI evidence cards.
6. Includes adequate backend and WebUI tests.

## Files to Inspect

```text
app/main.py
app/api/routes/retrieve.py
app/schemas/retrieval.py
app/services/retrieval_service.py
app/retrieval/evidence_mapper.py
app/integrations/lightrag_remote_adapter.py
WebUI files changed in the PR
tests changed in the PR
```

## Red Flags

Reject or request changes if the PR:

- calls LightRAG directly from WebUI
- adds duplicate `/api/v1/auth/*`
- adds a new retrieval service instead of using `RetrievalService`
- returns raw LightRAG chunks to the WebUI
- persists evidence without product justification
- restores `/query/retrieve` without an explicit product/API decision and tests
- makes side panel depend on answer text citations only
- hides LightRAG errors and shows stale evidence
- re-ranks evidence in WebUI without backend support
- mixes unrelated refactors into the PR

## Required Checks

- Run `python -m pytest -q`.
- Confirm OpenAPI shows `POST /retrieve`.
- Confirm `/query/retrieve` remains 404 unless intentionally restored.
- Confirm normal users cannot get debug output.
- Confirm admin can get debug output when requested.
- Confirm empty evidence returns 200.
- Confirm side panel has loading, empty, success, and error states.

## Review Output Format

Return:

```text
Verdict: APPROVE / REQUEST CHANGES

Summary:
- ...

Evidence:
- file -> function/route/schema

Blocking Issues:
- ...

Non-blocking Suggestions:
- ...

Test Coverage:
- ...
```
