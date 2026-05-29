# Removed Surface Map

| Removed item | Reason | Replacement |
|---|---|---|
| Repair UI/API | Duplicate recovery verb | Start internally refreshes/boots. |
| Recreate UI/API | Docker implementation detail | Start; optional private helper only. |
| Regenerate UI/API | File-writing implementation detail | Start writes env/compose internally. |
| Purge preview | Only supports removed hard purge | No product replacement. |
| Purge | Dangerous permanent delete | Safe Delete/archive. |
| Retrieval defaults UI | Runtime tuning bloat | Backend config -> domain.env. |
| Create auto-start | Mixes config and runtime boot | Create only; Start boot. |
