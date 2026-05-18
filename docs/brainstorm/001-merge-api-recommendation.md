Route explanation + merge recommendation
API Route	Method	What it does	Why it exists	Merge / simplify recommendation
/health	GET	Basic liveness check. Returns simple {"status": "ok"}.	Lets Docker, deploy scripts, or a load balancer know the API process is alive.	Keep, but very simple.
/health/readiness	GET	Readiness check. Currently returns simple {"status": "ready"}.	Should tell whether the app is ready to serve real traffic.	Maybe merge or improve. If it only returns static ready, it is redundant. Either merge into /health or make it check Postgres/Redis.
/auth/login	POST	Checks email/password and returns an access token.	Starts an authenticated CLI/TUI/API session.	Keep separate. Login is a distinct auth action.
/auth/me	GET	Returns the currently authenticated user.	Lets the TUI know who is logged in and what role they have.	Keep. Useful for session restore and role-aware UI.
/documents	GET	Lists ready documents for normal authenticated users.	User-facing document library.	Keep, but consider query params later. Could eventually become /documents?status=ready.
/documents/{document_id}	GET	Returns metadata for one ready document.	Used by document detail screen.	Keep. Clean REST shape.
/documents/{document_id}/structure	GET	Returns navigation/tree structure for a ready document.	Used for table of contents / section navigation.	Keep. Not redundant with page text.
/documents/{document_id}/pages/{page}	GET	Returns parsed text/content for one page.	Used for document viewer and citation inspection.	Keep. Not redundant with structure.
/admin/ping	GET	Confirms the caller is an admin and returns admin status/email.	Simple admin-auth smoke test.	Maybe redundant. Could be replaced by /auth/me if the TUI checks role there. Keep only if useful for admin diagnostics.
/admin/documents	GET	Lists all documents, including non-ready/admin-visible states.	Admin document management.	Possible merge with /documents. Could become /documents?scope=all or /documents?include_deleted=true, admin-only when broader than ready docs.
/admin/documents/upload	POST	Uploads a file, creates a document row, and usually creates/queues an indexing job.	Admin-only ingestion entry point.	Keep. Distinct write operation.
/admin/documents/{document_id}/index	POST	Queues indexing for a document.	Admin can trigger indexing.	Merge with reindex. Current code calls the same job enqueue service as reindex.
/admin/documents/{document_id}/reindex	POST	Queues indexing again for a document.	Admin can rebuild index artifacts.	Merge with index. Use one endpoint like POST /admin/documents/{id}/index-jobs with body `{ "mode": "index"
/admin/documents/{document_id}	DELETE	Deletes or soft-deletes a document.	Admin cleanup/removal.	Keep. Different HTTP method, clear resource semantics.
/admin/audit-logs	GET	Lists audit log records.	Admin observability/security trail.	Keep, or later merge into a generic logs endpoint.
/admin/query-logs	GET	Lists retrieval/query log records.	Admin observability for user questions and retrieval behavior.	Keep for clarity, or merge with audit logs under /admin/logs?type=query.
/query/retrieve	POST	Retrieves evidence/context only. Does not produce final answer.	Debugging retrieval quality and showing sources.	Keep. Important for RAG debugging and transparent TUI screens.
/query/answer	POST	Retrieves evidence and generates/returns an answer.	Main ask-question workflow.	Merge with /query. This overlaps with POST /query.
/query	POST	Shortcut for answer generation. In code it calls the same answer service as /query/answer.	Convenience endpoint.	Redundant. Pick one. I would keep /query as public/simple and deprecate /query/answer, or keep /query/answer for explicitness and remove /query.
/jobs	GET	Lists jobs.	Admin job monitor.	Keep.
/jobs/{job_id}	GET	Shows one job’s status/detail.	Admin can inspect indexing failures/progress.	Keep.
/jobs/{job_id}/retry	POST	Retries/reruns a failed or existing job.	Admin recovery path.	Keep, but consider naming as POST /jobs/{id}/actions/retry if you later add more job actions.
/graphs	GET	Proxies graph retrieval to the LightRAG service for a label.	Graph visualization/exploration.	Keep, but consider moving under /graph.
/graph/label/list	GET	Proxies all graph labels from LightRAG.	Label browser.	Can merge. Could become GET /graph/labels.
/graph/label/popular	GET	Proxies popular labels from LightRAG.	Helps TUI show useful graph starting points.	Can merge. Could become GET /graph/labels?sort=popular&limit=300.
/graph/label/search	GET	Proxies label search from LightRAG.	Lets user search graph labels.	Can merge. Could become GET /graph/labels?q=...&limit=50.

The documents route file shows the normal user document routes: list ready documents, get a document, get structure, and get page content. The admin route file shows upload, index, reindex, delete, list all documents, audit logs, and query logs; notably, index and reindex both call enqueue_index_document(...), which is why they are strong merge candidates. The jobs routes are cleanly separated into list, detail, and retry actions, so I would not merge those right now. The graph routes are proxy routes to LightRAG, so they do not write local graph tables; they only authenticate locally, then call the remote adapter.

Best merge candidates
Priority	Current routes	Problem	Recommended cleaner design
1	POST /query/answer and POST /query	They both return an answer using the same service path.	Keep one. My preference: keep POST /query for user-facing ask flow; keep POST /query/retrieve for evidence-only debugging.
2	POST /admin/documents/{id}/index and POST /admin/documents/{id}/reindex	Current code does the same enqueue operation for both.	Replace both with POST /admin/documents/{id}/index-jobs and optional body { "force": true } or { "mode": "reindex" }.
3	/graph/label/list, /graph/label/popular, /graph/label/search	Three routes for the same resource: graph labels.	Replace with GET /graph/labels?q=&sort=popular&limit=....
4	GET /documents and GET /admin/documents	Both list documents, but one is user-ready-only and one is admin-all.	Optional merge: `GET /documents?scope=ready
5	GET /admin/audit-logs and GET /admin/query-logs	Both are admin log readers.	Optional merge: `GET /admin/logs?type=audit
6	GET /health and GET /health/readiness	Both currently return static status.	Either merge, or make readiness actually check DB/Redis.
My recommended final route shape

For clean, junior-friendly API design:

Keep:
  GET  /health
  GET  /health/readiness        # only if it checks dependencies
  POST /auth/login
  GET  /auth/me

Documents:
  GET  /documents
  GET  /documents/{id}
  GET  /documents/{id}/structure
  GET  /documents/{id}/pages/{page}

Admin documents:
  POST   /admin/documents/upload
  POST   /admin/documents/{id}/index-jobs
  DELETE /admin/documents/{id}

Queries:
  POST /query/retrieve
  POST /query

Jobs:
  GET  /jobs
  GET  /jobs/{id}
  POST /jobs/{id}/retry

Graph:
  GET /graph
  GET /graph/labels

Observability:
  GET /admin/logs?type=audit
  GET /admin/logs?type=query

For this repo’s current stage, I would not over-merge everything immediately. I would only merge the obvious duplicates first:

1. /query/answer + /query
2. /admin/documents/{id}/index + /admin/documents/{id}/reindex
3. /graph/label/list + /graph/label/popular + /graph/label/search

That gives you less route entropy without making the API harder for junior engineers to understand.