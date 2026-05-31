# Context Engine Upload Workflow Simplification Package

This package locks in the simplified document upload/status architecture for Context Engine.

It is intended for a junior developer and coding agent working in:

```text
https://github.com/tabesink/context_engine.git
```

## Core simplification

Use this as the guiding rule:

```text
Upload creates a document and one operation.
The operation owns active progress.
The document owns final/current availability.
Processing-status is the only normal UI polling surface.
Jobs/worker/poller are internal machinery.
```

## Target product workflow

```text
Upload document.
Watch processing status.
Retry if failed.
Open when ready.
```

Everything else is internal machinery.

## Package contents

```text
README.md
00_architecture_decision_record.md
01_current_upload_workflow_map.md
02_target_low_entropy_upload_workflow.md
03_state_ownership_contract.md
04_endpoint_simplification_plan.md
05_worker_and_poller_responsibility_plan.md
06_phase_by_phase_implementation_plan.md
07_database_and_operation_model_plan.md
08_backend_service_boundary_plan.md
09_frontend_ui_wiring_plan.md
10_test_plan.md
11_risk_register_and_rollback.md
12_final_acceptance_criteria.md

api_contracts/
  upload_response_contract.json
  processing_status_response_contract.json
  retry_ingestion_response_contract.json

ui_contracts/
  documents_surface_status_rules.md
  polling_rules.md
  domain_surface_do_not_expose.md

templates/code/
  operation_status_models.py
  document_upload_service_contract.py
  document_ingestion_status_service.py
  remote_status_reconciler.py
  processing_status_presenter.py
  retry_ingestion_service.py

templates/alembic/
  0016_upload_workflow_operation_fields.py

agent_prompts/
  coding_agent_master_prompt.md
  phase_1_prompt.md
  phase_2_prompt.md
  phase_3_prompt.md
  phase_4_prompt.md
  phase_5_prompt.md

checklists/
  junior_dev_execution_checklist.md
  coding_agent_review_checklist.md

diagrams/
  current_upload_flow.txt
  target_upload_flow.txt
  worker_poller_status_flow.txt
```

## Non-goals

Do not remove the worker.
Do not remove the backend status poller.
Do not expose LightRAG raw pipeline internals as product concepts.
Do not add event sourcing or a detailed upload-stage table yet.
Do not build new UI against `/ingestion-status`.
Do not make `/jobs` the primary UI polling surface.

## Preferred public/admin surface

Normal UI:

```text
POST /admin/documents/upload
GET  /documents/{document_id}/processing-status
GET  /admin/documents/{document_id}/processing-status
GET  /admin/lightrag/domains/{domain_id}/documents/processing-status
GET  /admin/lightrag/domains/{domain_id}/processing-status
```

Admin diagnostics only:

```text
GET /jobs
GET /jobs/{job_id}
```

Manual recovery only:

```text
POST /admin/documents/{document_id}/refresh-status
```

Product-facing retry target:

```text
POST /admin/documents/{document_id}/retry-ingestion
```
