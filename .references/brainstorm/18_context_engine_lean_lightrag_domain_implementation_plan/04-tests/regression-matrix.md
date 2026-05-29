# Regression Matrix

| Area | Risk | Required regression test |
|---|---|---|
| Create no longer starts | Users expect running after create | Create returns configured/stopped and no Docker up call. |
| Start absorbs artifact refresh | Missing env/compose updates | Start writes env/compose before Docker up. |
| Provider key rotation | Running container uses stale key | Start uses latest secret value in generated env. |
| Embedding identity | Domain embedding changes accidentally | Start uses domain snapshot, not current default embedding. |
| Retrieval defaults removal | Env missing LightRAG defaults | Env writer pulls defaults from backend settings. |
| Delete safe retention | Accidental document deletion | Delete preserves document rows/assets. |
| Removed routes | Old UI/API calls break silently | Removed routes return 404/410; frontend no calls. |
| Purge removal | Storage accumulation | Document retention policy is documented. |
