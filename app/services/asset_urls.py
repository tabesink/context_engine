def document_asset_url(document_id: str, asset_id: str) -> str:
    return f"/documents/{document_id}/assets/{asset_id}"


def document_asset_thumbnail_url(
    document_id: str,
    asset_id: str,
    *,
    has_thumbnail: bool,
) -> str | None:
    if not has_thumbnail:
        return None
    return f"{document_asset_url(document_id, asset_id)}/thumbnail"
