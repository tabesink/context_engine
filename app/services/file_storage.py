from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings


class FileStorage:
    def __init__(self, root: Path | None = None):
        self.root = root or get_settings().storage_root
        self.root.mkdir(parents=True, exist_ok=True)

    def save_upload(self, upload: UploadFile) -> Path:
        suffix = Path(upload.filename or "document").suffix
        safe_name = f"{uuid4()}{suffix}"
        destination = self.root / safe_name
        with destination.open("wb") as target:
            while chunk := upload.file.read(1024 * 1024):
                target.write(chunk)
        return destination

