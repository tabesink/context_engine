from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.schemas.retrieval import RetrieveRequest, RetrieveResponse
from app.services.retrieval_service import RetrievalService
from app.storage.db import get_session
from app.storage.tables import UserRow

router = APIRouter(tags=["retrieval"])


@router.post("/retrieve")
def retrieve(
    request: RetrieveRequest,
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> RetrieveResponse:
    return RetrievalService(session).retrieve(request=request, user=user)
