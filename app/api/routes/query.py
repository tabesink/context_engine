from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.schemas.query import QueryRequest, QueryResponse, RetrieveResponse
from app.services.retrieval_service import RetrievalService
from app.storage.db import get_session
from app.storage.tables import UserRow

router = APIRouter(prefix="/query", tags=["query"])


@router.post("/retrieve")
def retrieve(
    request: QueryRequest,
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> RetrieveResponse:
    return RetrievalService(session).retrieve(request=request, user=user)


@router.post("/answer")
def answer(
    request: QueryRequest,
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> QueryResponse:
    return RetrievalService(session).answer(request=request, user=user)


@router.post("")
def query(
    request: QueryRequest,
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> QueryResponse:
    return RetrievalService(session).answer(request=request, user=user)

