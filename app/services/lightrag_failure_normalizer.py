import re

_MISSING_SECRET_KEY_PATTERN = re.compile(r"\b[A-Z][A-Z0-9_]{2,}\b")


def normalize_lightrag_failure_message(
    raw_message: str | None,
) -> tuple[str | None, list[str] | None]:
    message = str(raw_message).strip() if raw_message is not None else None
    if not message:
        return message, None
    missing_provider_secrets = _extract_missing_provider_secrets(message)
    if not missing_provider_secrets:
        return message, None
    plural = "s" if len(missing_provider_secrets) > 1 else ""
    friendly = (
        f"Missing provider secret{plural}: {', '.join(missing_provider_secrets)}. "
        "Configure it in AI Settings > Provider secrets and retry ingestion."
    )
    return friendly, missing_provider_secrets


def _extract_missing_provider_secrets(message: str) -> list[str]:
    tokens = _MISSING_SECRET_KEY_PATTERN.findall(message)
    candidates = sorted(
        {
            token
            for token in tokens
            if "_" in token and any(suffix in token for suffix in ("KEY", "TOKEN", "SECRET"))
        }
    )
    if not candidates:
        return []
    normalized = re.sub(r"[\[\]\(\)\{\}'\",:;]", " ", message).strip()
    words = [part for part in normalized.split() if part]
    if words and all(part in candidates for part in words):
        return candidates
    lowered = message.lower()
    if "missing" in lowered and ("key" in lowered or "secret" in lowered or "token" in lowered):
        return candidates
    return []
