from app.services.lightrag_failure_normalizer import normalize_lightrag_failure_message


def test_normalizer_returns_friendly_missing_secret_message() -> None:
    message, secrets = normalize_lightrag_failure_message(
        "LightRAG domain missing required provider secret OPENAI_API_KEY"
    )
    assert message == (
        "Missing provider secret: OPENAI_API_KEY. "
        "Configure it in AI Settings > Provider secrets and retry ingestion."
    )
    assert secrets == ["OPENAI_API_KEY"]


def test_normalizer_leaves_unknown_error_untouched() -> None:
    message, secrets = normalize_lightrag_failure_message("remote ingestion failed")
    assert message == "remote ingestion failed"
    assert secrets is None
