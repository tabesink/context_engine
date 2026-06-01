from pathlib import Path


def test_final_architecture_docs_cover_core_contracts() -> None:
    required_docs = {
        "docs/ARCHITECTURE_TARGET.md": [
            "Documents = uploaded files plus parsed local structure",
            "Domains = LightRAG runtime/workspace identity",
            "Operations = async work visible through product APIs",
        ],
        "docs/API_CONTRACTS.md": [
            "GET /documents/{document_id}/processing-status",
            "GET /operations",
            "POST /admin/lightrag-domains/{domain_id}/start",
        ],
        "docs/DOMAIN_LIFECYCLE.md": [
            "create",
            "start",
            "stop",
            "delete",
            "desired state",
            "observed runtime state",
        ],
        "docs/DOCUMENT_UPLOAD_WORKFLOW.md": [
            "register_upload",
            "parse_local_structure",
            "push_to_lightrag",
            "poll_remote_indexing",
            "processing-status",
        ],
    }

    for path, required_terms in required_docs.items():
        content = Path(path).read_text(encoding="utf-8")
        for term in required_terms:
            assert term in content, f"{path} is missing {term!r}"
