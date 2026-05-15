"""Admin upload workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def upload_document_flow(client: Any, file_path: Path) -> dict[str, Any]:
    upload = client.post_file(
        "/admin/documents/upload",
        field_name="file",
        filename=file_path.name,
        content=file_path.read_bytes(),
    )
    job = None
    if upload.get("job_id"):
        job = client.get(f"/jobs/{upload['job_id']}")
    return {"file": file_path.name, "upload": upload, "job": job}
