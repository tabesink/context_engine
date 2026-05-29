# Phase 2 Coding Agent Prompt

Implement Phase 2 only: promote LightRAG domains to first-class rows.

Tasks:

1. Rename/promote `lightrag_domain_lifecycle` to `lightrag_domains`.
2. Rename column `domain_id` to `id`.
3. Add nullable fields:
   - `display_name`
   - `health_status`
   - `base_url`
   - `container_name`
   - `host_port`
   - `embedding_profile_id`
   - `created_by_user_id`
4. Update ORM class:
   - `LightRAGDomainLifecycleRow` -> `LightRAGDomainRow`
5. Update services/repositories to use Domain terminology, not Lifecycle terminology.
6. Keep state vocabulary lean:
   - `creating`, `stopped`, `starting`, `running`, `stopping`, `failed`, `deleted`
7. Create operations for domain create/start/stop/delete.
8. Run data audit before adding FK from documents to domains.
9. Add tests.

Do not expose repair/recreate/regenerate/purge as normal UI actions.
Do not touch document relationship arrays in this phase.
