from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from app.core.config import get_settings


class FileStorage:
    def __init__(self, root: Path | None = None):
        self.root = root or get_settings().storage_root
        self.root.mkdir(parents=True, exist_ok=True)

    def save_upload(self, upload: UploadFile) -> Path:
        settings = get_settings()
        suffix = Path(upload.filename or "document").suffix
        safe_name = f"{uuid4()}{suffix}"
        destination = self.root / safe_name
        total_bytes = 0
        with destination.open("wb") as target:
            while chunk := upload.file.read(1024 * 1024):
                total_bytes += len(chunk)
                if total_bytes > settings.max_upload_bytes:
                    target.close()
                    destination.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail="Uploaded file exceeds MAX_UPLOAD_BYTES",
                    )
                target.write(chunk)
        return destination

