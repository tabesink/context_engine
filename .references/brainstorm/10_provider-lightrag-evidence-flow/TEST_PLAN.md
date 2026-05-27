# Test Plan

## Backend Provider Tests

- admin can create provider profile
- admin can update provider profile
- regular user forbidden
- unauthenticated user forbidden
- raw API key not returned
- masked key status returned
- provider test success/failure handled
- OpenAI-compatible base URL preserved

## LightRAG Domain Tests

- domain creation requires provider profile
- domain stores provider profile ID or snapshot
- domain stores embedding model and dimension
- domain env generation uses selected provider
- domain blocks embedding model change after ingestion
- domain can change LLM model if embedding is unchanged
- domain start/restart handles provider misconfig clearly

## Upload/Ingestion Tests

- admin upload requires lightrag_domain_id
- upload fails if domain is missing
- upload fails if domain provider not configured
- upload fails if domain not ready
- document stores domain and embedding model
- ingestion locks embedding model on first success
- ingestion sends chunks to correct LightRAG domain
- local structure/assets persist
- partial failure updates job status

## Retrieval Tests

- regular user can call `/retrieve`
- retrieval requires authentication
- selected domain is validated
- document filter belongs to selected domain
- evidence includes reference_id/document_id/document_title/source_path/chunk_id/page data
- include_assets returns asset records when available
- LightRAG unavailable returns clear error

## Workspace Tree Tests

- regular user can fetch workspace tree
- unauthenticated user cannot
- tree is scoped by domain
- tree includes ready documents
- processing/failed documents show safe status if included
- tree nodes can be linked to evidence IDs

## Frontend Tests

- settings route label is Provider
- provider page is admin-only
- API key field is masked after save
- regular user cannot access provider management UI
- upload UI requires selected domain
- chat sends selected domain ID
- chat uses `/retrieve` or approved streaming wrapper
- context panel renders mapped evidence
- workspace tree fetches backend endpoint
- empty evidence and failed retrieval states render gracefully
