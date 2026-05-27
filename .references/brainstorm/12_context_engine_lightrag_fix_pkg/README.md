# Context Engine — LightRAG Upload Fix Implementation Package

This package is a handoff for a junior developer and coding agent to cleanly fix the document upload failure:

> `LightRAG service unavailable`

Working diagnosis:

> The API/worker containers cannot resolve or connect to the managed LightRAG domain service name, e.g. `lightrag_fatigue`, even though the host machine can reach `127.0.0.1:9622`.

This is a Docker runtime boundary issue: host-to-container reachability is not the same as API-container-to-LightRAG-container reachability.

## Goal

Make LightRAG domain resolution, domain lifecycle, document upload validation, graph access, and ingestion use one lean backend contract:

```text
One domain registry -> one runtime URL resolver -> one health probe -> all upload/retrieval/graph/worker paths
```

Do not scatter host URL vs container URL decisions across services.

## Package contents

| File | Purpose |
|---|---|
| `docs/01_problem_diagnosis.md` | Explains the failure mode and why host `127.0.0.1` tests can be misleading. |
| `docs/02_target_architecture.md` | Defines the lean architecture after cleanup. |
| `docs/03_implementation_plan.md` | Step-by-step implementation plan divided into PR-sized phases. |
| `docs/04_file_change_map.md` | Concrete files to inspect/change and expected responsibilities. |
| `docs/05_acceptance_criteria.md` | Definition of done and pass/fail checks. |
| `runbooks/docker_dns_debug_runbook.md` | Commands to verify `lightrag_fatigue` DNS/reachability from API and worker containers. |
| `runbooks/domain_repair_runbook.md` | Manual and future automated domain repair flow. |
| `patch_skeletons/runtime_url_resolver.py` | Skeleton for dynamic host/container URL resolution. |
| `patch_skeletons/domain_health_probe.py` | Skeleton for centralized LightRAG health probing. |
| `patch_skeletons/admin_repair_endpoint.py` | Skeleton for `POST /admin/lightrag/domains/{domain_id}/repair`. |
| `tests/test_plan.md` | Unit/integration/manual test matrix. |
| `prompts/coding_agent_prompt.md` | Ready-to-paste coding-agent prompt. |
| `checklists/junior_dev_checklist.md` | Practical checklist for implementation and review. |

## Recommended implementation order

1. Confirm DNS/reachability from inside `api` and `worker`.
2. Add dynamic runtime URL resolution.
3. Fix generated Compose networking and aliases.
4. Add central health probe.
5. Add admin repair operation.
6. Wire upload/graph/retrieval/worker paths through the same resolver/probe.
7. Add tests and manual smoke checks.

## Non-goals

- Do not embed LightRAG directly into Context Engine.
- Do not make LightRAG a library dependency inside the API process.
- Do not introduce multiple new domain models.
- Do not create duplicate upload/retrieval flows.
- Do not make the frontend parse Docker details.

