# Agent Grill-Me + TDD Plan

## Decision Checklist

Before coding, lock these answers:

- Existing callers of `GET /lightrag/domains/{domain_id}/workspace-tree` keep the current full-tree behavior.
- WebUI should explicitly call `?depth=2&include_assets=true` for its first lightweight navigation integration.
- `depth` is measured from the root domain node, where root is `0`.
- `include_assets=false` removes asset nodes from the tree; it does not change document detail endpoints.
- The tree remains navigational only. Full page and chunk text stay behind document detail APIs.

## TDD Tracer Bullets

Work vertically. Do not write all tests first.

1. RED: `GET /lightrag/domains/{domain_id}/workspace-tree?depth=2` returns a full deep tree.
   GREEN: thread `depth` from the route to the service and stop adding children once max depth is reached.

2. RED: default workspace-tree behavior changes after adding depth support.
   GREEN: make `depth` optional and preserve full tree behavior when omitted.

3. RED: `include_assets=false` still returns asset nodes.
   GREEN: gate `_asset_node()` creation in section, page, and loose-reference paths.

4. RED: the endpoint still scans all ready documents and filters domain metadata in Python.
   GREEN: move LightRAG domain filtering into `DocumentRepository.list_ready_by_lightrag_domain()` using SQL JSON predicates.

5. RED: legacy documents with `metadata.lightrag.domain` disappear.
   GREEN: keep an `OR` predicate for both `domain_id` and legacy `domain`.

6. RED: workspace-tree response leaks full page text or the tail of chunk text.
   GREEN: keep page text out of nodes, strip `metadata.text`, and keep chunk node titles as compact snippets.

7. RED: frontend contract is unclear in docs.
   GREEN: document the recommended WebUI call and lazy-detail endpoints in the API contract docs.

## Grill-Me Questions

- What does `depth=2` include, exactly, and why?
- What happens when `depth` is omitted?
- Why is `include_assets` defaulting to `true` instead of `false`?
- Which endpoints should the frontend call when a user opens a page, section, or chunk?
- How do we know full page text and chunk tail text do not leak into the navigation tree?
- Does the repository query still include legacy LightRAG domain metadata?

## Guardrails

- Prefer API-level tests for the public contract.
- Keep node kinds unchanged.
- Do not add document endpoint behavior unless a test demonstrates the workspace-tree contract needs it.
- Do not edit historical brainstorm material outside this contract folder.
- Keep docs focused on the stable frontend contract, not internal implementation details.
