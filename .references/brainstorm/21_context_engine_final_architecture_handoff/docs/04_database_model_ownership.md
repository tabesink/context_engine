# 04 — Database Model Ownership

## Target Database Ownership

```text
users                          Core auth/user ownership
documents                      Core document metadata/status
document_sections              Core local navigation
document_pages                 Core page navigation
document_blocks                Core parsed structure, but heavy
document_assets                Core evidence images/tables/assets
document_source_chunks         Core citation/source mapping
jobs                           Core internal async table; exposed as operations
audit_logs                     Core/admin accountability
query_logs                     Useful; privacy-sensitive
lightrag_domains               Core domain registry
domain lifecycle table         Candidate for deprecation if duplicated by operations/audit
ai_model_profiles              Optional if env owns provider config
ai_model_settings              Optional if env owns defaults
ai_provider_secrets            Optional if env owns secrets
```

## Target Schema Relationship

```text
┌────────────────────┐
│ users              │
├────────────────────┤
│ id                 │
│ email              │
│ username           │
│ role               │
└─────────┬──────────┘
          │ owns
          ▼
┌──────────────────────────────┐
│ documents                    │
├──────────────────────────────┤
│ id                           │
│ owner_id                     │
│ filename                     │
│ storage_path                 │
│ status                       │
│ processing_stage             │
│ lightrag_domain_id           │
│ active_index_version         │
└───────┬────────────┬─────────┘
        │            │
        │            ▼
        │   ┌────────────────────┐
        │   │ local structure    │
        │   ├────────────────────┤
        │   │ sections           │
        │   │ pages              │
        │   │ blocks             │
        │   │ assets             │
        │   │ source_chunks      │
        │   └────────────────────┘
        │
        ▼
┌──────────────────────────────┐
│ jobs                         │
├──────────────────────────────┤
│ id                           │
│ kind                         │
│ status                       │
│ stage                        │
│ progress                     │
│ document_id                  │
│ lightrag_domain_id           │
│ metadata                     │
└──────────────────────────────┘
```

## LightRAG Domain Source of Truth

```text
┌──────────────────────────────┐
│ lightrag_domains             │
├──────────────────────────────┤
│ domain_id                    │
│ display_name                 │
│ desired_state                │
│ host_port                    │
│ container_name               │
│ embedding_model              │
│ created_at / updated_at      │
└──────────────┬───────────────┘
               │ observed by
               ▼
┌──────────────────────────────┐
│ runtime health check         │
├──────────────────────────────┤
│ reachable                    │
│ health                       │
│ last_checked_at              │
└──────────────────────────────┘
```

## Migration Guardrails

Do not drop tables in the first implementation pass.

Use this sequence:

```text
1. Document ownership.
2. Stop adding new reads.
3. Stop frontend usage.
4. Stop backend writes.
5. Keep compatibility adapters.
6. Add migration only after no production code depends on the table/field.
```

## Candidate Deprecations

### lightrag_domain_lifecycle

Can be deprecated if:

```text
operations records lifecycle action status
and audit_logs records actor/action/resource
```

### ai_model_profiles / ai_model_settings / ai_provider_secrets

Can be downgraded to optional/advanced if:

```text
env/domain.env owns provider config
provider UI is read-only diagnostics
no runtime mutation of retrieval defaults is allowed
```
