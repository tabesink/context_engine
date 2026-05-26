from fastapi import APIRouter, Depends, HTTPException
import httpx
import redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.storage.db import get_session

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/readiness")
def readiness(session: Session = Depends(get_session)) -> dict:
    settings = get_settings()
    checks: dict[str, str] = {}

    try:
        session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc.__class__.__name__}"

    if settings.index_jobs_inline:
        checks["redis"] = "skipped"
    else:
        try:
            redis.Redis.from_url(settings.redis_url).ping()
            checks["redis"] = "ok"
        except Exception as exc:
            checks["redis"] = f"error: {exc.__class__.__name__}"

    manifest_paths = [
        path
        for path in (settings.lightrag_domain_manifest, settings.lightrag_domains_manifest)
        if path is not None
    ]
    if any(path.is_file() for path in manifest_paths):
        checks["lightrag"] = "manifest"
    else:
        try:
            with httpx.Client(
                base_url=settings.lightrag_base_url.rstrip("/"),
                timeout=settings.lightrag_timeout_seconds,
            ) as client:
                response = client.get("/health")
                response.raise_for_status()
            checks["lightrag"] = "ok"
        except Exception as exc:
            checks["lightrag"] = f"error: {exc.__class__.__name__}"

    if any(value.startswith("error:") for value in checks.values()):
        raise HTTPException(
            status_code=503,
            detail={"status": "not_ready", "checks": checks},
        )

    return {"status": "ready", "checks": checks}

