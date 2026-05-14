# LightRAG Implementation And Test Coverage

This document records the current LightRAG behavior and the test slices that protect it. Future changes should still follow a vertical red-green-refactor workflow: add one behavior test, implement the smallest useful code path, then repeat.

Tests verify behavior through public interfaces where possible:

- FastAPI routes through `TestClient`
- CLI behavior through the fake API client only if the API surface changes
- adapter behavior through mocked HTTP responses, not a live LightRAG service

## Public Behaviors To Protect

1. Existing local behavior still works when `LIGHTRAG_ENABLED=false`.
2. Admin upload remains forbidden to normal users.
3. Admin upload can forward a file to mocked LightRAG when `LIGHTRAG_ENABLED=true`.
4. Query retrieval returns normalized evidence from mocked LightRAG.
5. Graph proxy routes return proxied graph data from mocked LightRAG.
6. LightRAG failures return stable app-level errors.

## Covered Cycle 1: Contract Files Exist

Behavior:

The repo documents the normalized LightRAG HTTP boundary.

Test:

- Keep this as a lightweight file existence/content test only if the team wants docs covered.
- Otherwise verify manually and move to the first app behavior.

Implementation:

- Add `external/lightrag/contract/openapi.yaml`.
- Add response examples under `external/lightrag/contract/examples/`.

## Covered Cycle 2: Local Path Is Still Default

Behavior:

With `LIGHTRAG_ENABLED=false`, existing upload and query flow should continue to pass.

Test:

- Use existing `tests/test_api.py` behavior as the regression test.
- Ensure env defaults keep remote LightRAG disabled unless configured otherwise.

Implementation:

- Add settings with safe defaults.
- Do not wire remote code into the default path yet.

## Covered Cycle 3: Domain Manifest Fallback

Behavior:

When no domain manifest exists, `context_engine` resolves the default domain from `LIGHTRAG_BASE_URL`.

Test:

- Instantiate the domain resolver with a missing manifest path.
- Assert default domain/base URL are returned.

Implementation:

- Add `app/integrations/lightrag_domains.py`.
- Keep it read-only.

## Covered Cycle 4: Remote Adapter Query Mapping

Behavior:

Given a mocked LightRAG `/query/data` response, the adapter returns existing `Evidence` objects.

Test:

- Use an `httpx` mock transport or injected client.
- Mock `/query/data`.
- Assert evidence text, score, document ID, page refs, and metadata are normalized.

Implementation:

- Add `app/integrations/lightrag_remote_adapter.py`.
- Add typed adapter errors.
- Add mode mapping.

## Covered Cycle 5: Query Route Uses Remote LightRAG

Behavior:

With `LIGHTRAG_ENABLED=true`, `POST /query/retrieve` returns evidence from mocked LightRAG.

Test:

- Exercise the public FastAPI route with `TestClient`.
- Seed users through existing helpers.
- Mock the adapter or HTTP transport at the boundary.

Implementation:

- Add a remote semantic retrieval engine or wire `RetrievalService` to choose the remote path.
- Preserve local fallback for disabled mode.

## Covered Cycle 6: Admin Upload Forwarding

Behavior:

With `LIGHTRAG_ENABLED=true`, admin upload creates a local document mirror and forwards the file to LightRAG.

Test:

- Use `POST /admin/documents/upload` with an admin token.
- Mock LightRAG upload response.
- Assert response includes local document information and external metadata.

Implementation:

- Extend document model/repository minimally.
- Store external engine/domain/document/status fields.
- Record audit metadata.

## Covered Cycle 7: Non-Admin Upload Stays Forbidden

Behavior:

Normal users cannot upload documents even when LightRAG is enabled.

Test:

- Exercise `POST /admin/documents/upload` with a normal user token.
- Assert `403`.

Implementation:

- No new implementation should be needed if `require_admin` remains the route dependency.

## Covered Cycle 8: Graph Proxy

Behavior:

Authenticated users can request graph data through `context_engine`; the app proxies LightRAG graph data.

Test:

- Exercise routes such as `GET /graphs` and `GET /graph/label/list`.
- Mock remote graph response.
- Assert the proxied response and query parameters.

Implementation:

- Add `app/api/routes/lightrag.py`.
- Include the router in `app/main.py`.
- Keep graph edits out of v1.

## Covered Cycle 9: Failure Mapping

Behavior:

Remote LightRAG timeout, invalid JSON, and 5xx responses become stable app-level errors.

Test:

- Mock timeout.
- Mock invalid JSON.
- Mock 500 response.

Implementation:

- Complete adapter error handling.
- Translate adapter errors at route/service boundaries.

## Refactor Pass

After all tests are green:

- Remove duplication in request/response normalization.
- Keep adapter interface small.
- Keep LightRAG-specific response quirks hidden from routes and services.
- Run the full test suite after each refactor step.

## Testing Boundaries

Prefer:

- route-level integration tests for user/admin behavior
- adapter tests with mocked HTTP
- settings/domain resolver tests for deterministic config behavior

Avoid:

- tests that import LightRAG internals
- tests that require Docker or a live LightRAG service
- tests coupled to private helper methods
- broad tests that assert every internal call shape
