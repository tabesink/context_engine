# Target API Surface

## Keep lifecycle routes

```text
GET    /admin/lightrag/domains
POST   /admin/lightrag/domains
GET    /admin/lightrag/domains/{domain_id}
POST   /admin/lightrag/domains/{domain_id}/up
POST   /admin/lightrag/domains/{domain_id}/down
DELETE /admin/lightrag/domains/{domain_id}
GET    /lightrag/domains
```

## Remove lifecycle routes

```text
POST   /admin/lightrag/domains/{domain_id}/repair
POST   /admin/lightrag/domains/{domain_id}/recreate
POST   /admin/lightrag/domains/{domain_id}/regenerate
POST   /admin/lightrag/domains/{domain_id}/purge-preview
DELETE /admin/lightrag/domains/{domain_id}/purge
```

## Target create request

```json
{
  "domain_id": "fatigue",
  "display_name": "Fatigue Manuals",
  "embedding_profile_id": "openai-text-embedding-3-small",
  "host_port": 9622,
  "make_default": false
}
```

If auto-port is used, omit `host_port`.

## Removed create request fields

```text
start
top_k
chunk_top_k
chunk_rerank_top_k
max_token_for_text_unit
max_token_for_global_context
max_token_for_local_context
```

## Target create response

Return the domain configuration and status. The status should be `configured` or `stopped`, not `running`, because Create no longer starts the container.
