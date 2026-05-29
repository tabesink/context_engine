from app.services.asset_urls import document_asset_thumbnail_url, document_asset_url


def test_document_asset_url_preserves_simple_ids() -> None:
    assert document_asset_url("doc-1", "asset-1") == "/documents/doc-1/assets/asset-1"
    assert (
        document_asset_thumbnail_url("doc-1", "asset-1")
        == "/documents/doc-1/assets/asset-1/thumbnail"
    )


def test_document_asset_url_escapes_path_components() -> None:
    assert document_asset_url("doc/with space", "asset#1") == (
        "/documents/doc%2Fwith%20space/assets/asset%231"
    )
    assert document_asset_thumbnail_url("doc/with space", "asset#1") == (
        "/documents/doc%2Fwith%20space/assets/asset%231/thumbnail"
    )
