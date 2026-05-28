# Definition of Done

A phase is done only when:

1. It implements only the approved phase scope.
2. It has a clear phase report.
3. It preserves Context Engine as the single API/auth boundary.
4. It does not introduce direct frontend LightRAG calls.
5. It respects admin-write / user-read boundaries.
6. It follows the app design rules.
7. It avoids duplicate components, stores, and API clients.
8. It runs validation commands or documents pre-existing failures.
9. It leaves the next phase easier, not harder.

The full UI rollout is done only when:

- Admin can manage LightRAG domains from a clear settings surface.
- Admin can see domain processing/runtime status.
- Admin can see document processing status.
- Admin can inspect jobs/events.
- Regular users can see safe indexing status.
- Chat retrieval still works.
- Workspace tree and Source Navigator still work.
- Status polling is deduplicated and does not overload LightRAG.
- Raw LightRAG metadata is not a frontend display contract.
- Redundant lifecycle verbs are hidden, clarified, or deferred behind advanced controls.
