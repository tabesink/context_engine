from pathlib import Path

import pytest
from fastapi import HTTPException

from app.document_processing.models import DocumentAsset
from app.services.document_asset_service import DocumentAssetService


class FakeAccessPolicy:
    def __init__(self) -> None:
        self.seen_document_id: str | None = None
        self.seen_user = None

    def get_readable_document_or_404(self, *, user, document_id: str):
        self.seen_user = user
        self.seen_document_id = document_id
        return object()


class FakeAssets:
    def __init__(self, asset: DocumentAsset | None) -> None:
        self.asset = asset

    def get_asset(self, document_id: str, asset_id: str) -> DocumentAsset | None:
        if self.asset and self.asset.document_id == document_id and self.asset.asset_id == asset_id:
            return self.asset
        return None


def test_document_asset_service_returns_streamable_authenticated_asset(tmp_path: Path) -> None:
    asset_path = tmp_path / "documents" / "doc-1" / "assets" / "asset.png"
    asset_path.parent.mkdir(parents=True)
    asset_path.write_bytes(b"png")
    access_policy = FakeAccessPolicy()
    service = DocumentAssetService(
        access_policy=access_policy,
        assets=FakeAssets(
            DocumentAsset(
                asset_id="asset-1",
                document_id="doc-1",
                asset_type="figure",
                storage_path=str(asset_path),
                content_hash="hash-1",
            )
        ),
        storage_root=tmp_path,
    )

    user = object()
    asset = service.get_asset_file(user=user, document_id="doc-1", asset_id="asset-1")

    assert access_policy.seen_document_id == "doc-1"
    assert access_policy.seen_user is user
    assert asset.path == asset_path
    assert asset.media_type == "image/png"


def test_document_asset_service_rejects_missing_files(tmp_path: Path) -> None:
    missing_path = tmp_path / "documents" / "doc-1" / "assets" / "missing.png"
    service = DocumentAssetService(
        access_policy=FakeAccessPolicy(),
        assets=FakeAssets(
            DocumentAsset(
                asset_id="asset-1",
                document_id="doc-1",
                asset_type="figure",
                storage_path=str(missing_path),
                content_hash="hash-1",
            )
        ),
        storage_root=tmp_path,
    )

    with pytest.raises(FileNotFoundError):
        service.get_asset_file(user=object(), document_id="doc-1", asset_id="asset-1")


def test_document_asset_service_rejects_paths_outside_storage_root(tmp_path: Path) -> None:
    storage_root = tmp_path / "storage"
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"png")
    service = DocumentAssetService(
        access_policy=FakeAccessPolicy(),
        assets=FakeAssets(
            DocumentAsset(
                asset_id="asset-1",
                document_id="doc-1",
                asset_type="figure",
                storage_path=str(outside),
                content_hash="hash-1",
            )
        ),
        storage_root=storage_root,
    )

    with pytest.raises(HTTPException) as exc_info:
        service.get_asset_file(user=object(), document_id="doc-1", asset_id="asset-1")

    assert exc_info.value.status_code == 404
