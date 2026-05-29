# Final Endpoint Map

## Keep

```text
GET    /admin/lightrag/domains
POST   /admin/lightrag/domains
GET    /admin/lightrag/domains/{domain_id}
POST   /admin/lightrag/domains/{domain_id}/up
POST   /admin/lightrag/domains/{domain_id}/down
DELETE /admin/lightrag/domains/{domain_id}
GET    /lightrag/domains
```

## Remove

```text
POST   /admin/lightrag/domains/{domain_id}/repair
POST   /admin/lightrag/domains/{domain_id}/recreate
POST   /admin/lightrag/domains/{domain_id}/regenerate
POST   /admin/lightrag/domains/{domain_id}/purge-preview
DELETE /admin/lightrag/domains/{domain_id}/purge
```
