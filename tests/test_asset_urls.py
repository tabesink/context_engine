from app.services.asset_urls import document_asset_thumbnail_url, document_asset_url


def test_document_asset_urls_match_existing_route_contract() -> None:
    assert document_asset_url("doc-1", "asset-1") == "/documents/doc-1/assets/asset-1"
    assert (
        document_asset_thumbnail_url("doc-1", "asset-1", has_thumbnail=True)
        == "/documents/doc-1/assets/asset-1/thumbnail"
    )
    assert document_asset_thumbnail_url("doc-1", "asset-1", has_thumbnail=False) is None
