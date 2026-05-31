# Coding Agent Master Prompt

You are working in `https://github.com/tabesink/context_engine.git`.

Implement the accepted upload workflow simplification. Do not make a big-bang refactor.

Guiding rule:

```text
Upload creates a document and one operation.
The operation owns active progress.
The document owns final/current availability.
Processing-status is the only normal UI polling surface.
Jobs/worker/poller are internal machinery.
```

Before coding, run:

```bash
rg "upload|reingest|refresh-status|ingestion-status|processing-status" app tests
rg "document_ingest|JobStatus|jobs|enqueue_document_ingest" app tests
rg "status_poller|poll_lightrag|refresh_pending_lightrag" app tests
rg "metadata.*lightrag|lightrag.*status" app tests
```

Implement one phase per PR.

Do not:

```text
Do not remove worker.
Do not remove poller.
Do not build new UI against ingestion-status.
Do not make jobs endpoint the primary UI status path.
Do not make metadata.lightrag.status authoritative.
Do not expose Upload/View Documents from domain lifecycle card/menu.
```

Run tests before finishing:

```bash
pytest
python -m alembic -c migrations/alembic.ini upgrade head
```

Adjust Alembic command if the repo uses a different path.
