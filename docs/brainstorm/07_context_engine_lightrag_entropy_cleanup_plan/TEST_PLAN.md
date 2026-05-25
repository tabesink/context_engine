# Test Plan: Mandatory LightRAG Semantic Retrieval

## 1. Config validation tests

Add/update tests to prove:

- `LIGHTRAG_ENABLED` defaults to true.
- `LIGHTRAG_ENABLED=false` raises a clear config error.
- Missing LightRAG base URL/domain config raises a clear config error.
- `.env.example` shows LightRAG as required.

Suggested test names:

```text
test_lightrag_enabled_defaults_true
test_lightrag_disabled_is_invalid
test_missing_lightrag_config_is_invalid
```

## 2. Retrieval routing tests

Add/update tests to prove:

- `semantic` mode calls `LightRAGRemoteRetrievalEngine`.
- `semantic` mode does not call `NavigationRetrievalEngine` as fallback.
- `hybrid` mode calls LightRAG and navigation.
- `navigation` mode calls only navigation.
- `auto` mode calls LightRAG first.
- LightRAG failure returns a clear error for semantic/hybrid/auto.

Suggested test names:

```text
test_semantic_mode_uses_remote_lightrag_only
test_semantic_mode_does_not_fallback_to_navigation
test_hybrid_mode_merges_lightrag_and_navigation
test_navigation_mode_uses_navigation_only
test_auto_mode_is_lightrag_first
test_lightrag_failure_does_not_silent_fallback
```

## 3. Upload and ingestion tests

Add/update tests to prove:

- Upload requires LightRAG config/domain.
- Upload queues LightRAG ingestion, not local semantic indexing.
- Structure-aware parse failure behavior is explicit.
- Unknown LightRAG status does not normalize to indexing.

Suggested test names:

```text
test_upload_requires_lightrag_domain
test_upload_queues_lightrag_ingestion
test_upload_does_not_queue_local_semantic_indexing
test_structure_failure_marks_ingestion_failed
test_unknown_lightrag_status_is_error
```

## 4. Regression tests to keep

Ensure existing behavior still passes for:

- `/documents`
- `/documents/{document_id}`
- `/documents/{document_id}/structure`
- `/documents/{document_id}/pages/{page_number}`
- `/documents/{document_id}/assets/{asset_id}`
- `/documents/{document_id}/assets/{asset_id}/thumbnail`
- admin upload authorization
- normal user retrieval against ready documents
- admin-only job/log/domain routes

## 5. Search-based assertions

As part of review, run:

```bash
rg "semantic_engine=self.navigation_engine"
rg "SemanticIndexBuilder"
rg "replace_semantic_chunks"
rg "list_semantic_chunks"
rg "allow_general_fallback"
rg "LIGHTRAG_ENABLED"
```

Expected result:

- No runtime use of local semantic indexing.
- No misleading semantic-to-navigation wiring.
- Any remaining `LIGHTRAG_ENABLED` reference validates that it must be true or documents compatibility.
