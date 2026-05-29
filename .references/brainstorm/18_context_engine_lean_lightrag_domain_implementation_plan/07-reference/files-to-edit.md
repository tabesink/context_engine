# Files To Edit

## Frontend

```text
client/src/components/settings/panels/KnowledgeGraphSettingsPanel.tsx
client/src/components/settings/lightrag-domains/CreateDomainForm.tsx
client/src/components/settings/lightrag-domains/DomainLifecycleCard.tsx
client/src/lib/api/knowledge-graph-admin.ts
client/src/types/lightrag.ts
```

## Backend routes/schemas

```text
app/api/routes/lightrag_admin.py
app/lightrag_deploy/models.py
```

## Backend services/deploy

```text
app/lightrag_deploy/service.py
app/lightrag_deploy/settings.py
app/lightrag_deploy/compose.py
app/services/model_profile_resolver.py
app/services/lightrag_runtime_config_resolver.py  # new optional file
```

## Settings/docs/tests

```text
app/core/config.py
.env.example
tests/
README.md
CONTEXT.md
docs/
```
