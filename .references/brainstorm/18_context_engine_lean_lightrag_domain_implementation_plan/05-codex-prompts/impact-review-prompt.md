# Impact Review Prompt

```text
Before implementing, audit the Context Engine repo for the LightRAG lifecycle simplification.

Find every use of:
- repair
- recreate
- regenerate
- purge
- purgePreview
- purge-preview
- top_k
- chunk_top_k
- chunk_rerank_top_k
- max_token_for
- retrieval_defaults
- retrievalDefaults
- start:true
- request.start

Classify each result:
- frontend UI
- frontend API/type
- backend route
- backend service
- backend model/schema
- env writer/settings
- test
- docs

Then produce a risk report and recommend exact edit order.

Do not implement until this report is complete.
```
