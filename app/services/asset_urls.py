from urllib.parse import quote


def document_asset_url(document_id: str, asset_id: str) -> str:
    return f"/documents/{quote(document_id, safe='')}/assets/{quote(asset_id, safe='')}"


def document_asset_thumbnail_url(document_id: str, asset_id: str) -> str:
    return f"{document_asset_url(document_id, asset_id)}/thumbnail"
