import pytest
from pydantic import ValidationError

from cli.query_payload import build_query_payload


def test_build_query_payload_uses_backend_query_schema_fields() -> None:
    payload = build_query_payload(
        query="install steps",
        mode="auto",
        top_k=8,
        include_debug=True,
        allow_general_fallback=False,
        document_ids=["doc-1"],
    )

    assert payload == {
        "query": "install steps",
        "mode": "auto",
        "document_ids": ["doc-1"],
        "top_k": 8,
        "include_debug": True,
        "allow_general_fallback": False,
    }


def test_build_query_payload_omits_empty_document_filter() -> None:
    payload = build_query_payload(
        query="install steps",
        mode="auto",
        top_k=8,
        include_debug=False,
        allow_general_fallback=False,
    )

    assert "document_ids" not in payload


def test_build_query_payload_validates_backend_constraints() -> None:
    with pytest.raises(ValidationError):
        build_query_payload(
            query="install steps",
            mode="auto",
            top_k=31,
            include_debug=False,
            allow_general_fallback=False,
        )
