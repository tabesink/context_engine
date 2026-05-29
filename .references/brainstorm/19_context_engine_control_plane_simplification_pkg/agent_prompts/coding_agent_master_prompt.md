# Coding Agent Master Prompt

You are working in `https://github.com/tabesink/context_engine.git`.

Your task is to simplify the Context Engine control-plane storage model without removing product capability.

Follow these principles:

1. Do not make a big-bang refactor.
2. Use expand-migrate-contract migrations.
3. Keep route handlers thin.
4. Centralize state transitions.
5. Preserve current API behavior unless the phase explicitly changes it.
6. Keep LightRAG domains as first-class product objects.
7. Use one Operation model for document/domain/provider/system work.
8. Do not use metadata JSON as a hidden status machine.
9. Remove duplicate document relationship arrays only after read APIs derive them from canonical scalar relationships.
10. Normal UI lifecycle vocabulary must be Create / Start / Stop / Delete.

First, run these searches:

```bash
rg "JobRow|JobStatus|jobs|document_id" app tests migrations
rg "LightRAGDomainLifecycleRow|lightrag_domain_lifecycle|domain_lifecycle|domain_id" app tests migrations
rg "block_ids|child_section_ids|asset_ids" app tests migrations
rg "ai_model_settings|AIModelSettingsRow" app tests migrations
```

Then implement one phase only. Do not mix phases in one PR.

Before finishing, run:

```bash
pytest
python -m alembic -c migrations/alembic.ini upgrade head
```

If the repo uses a different Alembic path, use the repo's existing documented command.
