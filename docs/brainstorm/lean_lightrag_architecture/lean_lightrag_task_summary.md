# Final Task Summary

## Title

Add a lean external LightRAG retrieval/graph service boundary to `context_engine`.

## Summary

Modify the `context_engine` master codebase so it can use an independently deployed LightRAG service for context retrieval and graph visualization only.

Do not merge LightRAG internals into `context_engine`.

Do not copy the full `easy-deploy-lightrag` server, UI, auth, conversations, or SQLite control plane.

Use `easy-deploy-lightrag` only as a reference for:

```text
domain deployment scripts
domain manifest shape
health checks
graph API ideas
archive-before-delete behavior
```

## Architecture

`context_engine` owns:

```text
users
auth
admin permissions
admin-only upload
document mirror records
retrieval settings
query routes
graph proxy routes
audit/query logs
```

External LightRAG owns:

```text
document ingestion
semantic/context retrieval
graph storage
graph visualization data
vector/graph internals
```

Communication is HTTP only.

## Implement in v1

```text
1. LightRAGRemoteAdapter
2. LightRAG domain manifest reader
3. admin-only upload forwarding
4. context retrieval through /query/context
5. graph proxy routes
6. retrieval settings from environment + optional JSONB profile
7. deployment wrapper under external/lightrag
8. tests using mocked LightRAG responses
```

## Do not implement in v1

```text
PageIndex
local semantic index
hybrid merger
LLM router
graph editing
LightRAG WebUI
LightRAG auth
conversations inside LightRAG
Neo4j inside context_engine
```

## Strongest Recommendation

Build around one contract file first:

```text
external/lightrag/contract/openapi.yaml
```

Then:

```text
external/lightrag must satisfy the contract
context_engine adapter consumes the contract
tests mock the contract
```
