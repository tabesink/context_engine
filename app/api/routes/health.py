from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.services.readiness_service import ReadinessService
from app.storage.db import get_session

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/readiness")
def readiness(session: Session = Depends(get_session)) -> dict:
    settings = get_settings()
    report = ReadinessService(settings=settings).check(session=session)
    payload = {"status": report.status, "services": report.services, "details": report.details}
    if report.warnings:
        payload["warnings"] = report.warnings
    if report.status != "ready":
        return JSONResponse(status_code=503, content=payload)
    return payload

