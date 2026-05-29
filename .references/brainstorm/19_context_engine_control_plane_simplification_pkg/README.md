# Context Engine Control-Plane Simplification Package

This package is a phased implementation handoff for simplifying the Context Engine runtime database/control-plane model.

It is written for a coding agent and junior developer working on:

- `https://github.com/tabesink/context_engine.git`
- FastAPI backend
- SQLAlchemy ORM in `app/storage/tables.py`
- Alembic migrations in `migrations/alembic/versions`
- Domain models in `app/domain/models.py`

## Main goal

Reduce technical entropy without removing product capability.

The target is not fewer tables at all costs. The target is clearer ownership:

```text
Document        = stable uploaded file registry + current availability
LightRAG Domain = first-class runtime/control-plane object
Operation       = all async or long-running work
Audit Log       = immutable admin/security history
Query Log       = retrieval telemetry
Document Read Model = local navigation structure and assets
AI Config       = provider/model/secrets control plane
```

## What this package contains

```text
README.md
00_architecture_decision_record.md
01_phase_by_phase_implementation_plan.md
02_schema_target_ascii.md
03_state_ownership_contract.md
04_database_migration_strategy.md
05_backend_touchpoints.md
06_api_contract_plan.md
07_test_plan.md
08_risk_register_and_rollback.md
09_final_acceptance_criteria.md

checklists/
  junior_dev_execution_checklist.md
  coding_agent_review_checklist.md

diagrams/
  current_vs_target_control_plane.txt
  operation_state_flow.txt

templates/alembic/
  0010_phase1_add_operation_columns.py
  0011_phase2_promote_lightrag_domains.py
  0012_phase3_drop_duplicate_document_relationship_arrays.py

templates/code/
  operation_models.py
  domain_models.py
  repository_contracts.py
  status_rollup_rules.py

agent_prompts/
  coding_agent_master_prompt.md
  phase_1_prompt.md
  phase_2_prompt.md
  phase_3_prompt.md
```

## Implementation rule

Do not implement this as one large PR.

Use separate PRs:

```text
PR 1: State ownership contract + add operation compatibility columns
PR 2: Migrate job service/repository to Operation terminology
PR 3: Promote LightRAG domain lifecycle into first-class lightrag_domains
PR 4: Remove duplicate document relationship array writes/reads
PR 5: Optional settings cleanup / rename ai_model_settings later
```

## Non-goals

Do not collapse the document navigation model into one JSON blob.
Do not remove `query_logs` unless analytics/privacy requirements are clarified.
Do not remove `audit_logs`; keep it as immutable history.
Do not make runtime retrieval defaults mutable in the UI; keep those in domain `.env` / domain config.
Do not reintroduce legacy navigation tables dropped by older migrations.
