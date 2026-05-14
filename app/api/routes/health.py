from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/readiness")
def readiness() -> dict[str, str]:
    return {"status": "ready"}

