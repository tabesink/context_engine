from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.errors import unauthorized
from app.core.security import create_access_token, verify_password
from app.domain.models import UserRole
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.storage.db import get_session
from app.storage.repositories.users import UserRepository
from app.storage.tables import UserRow

router = APIRouter(prefix="/auth", tags=["auth"])


def user_response(user: UserRow) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        role=UserRole(user.role),
        is_active=user.is_active,
    )


@router.post("/login")
def login(request: LoginRequest, session: Session = Depends(get_session)) -> TokenResponse:
    user = UserRepository(session).get_by_email(request.email)
    if not user or not verify_password(request.password, user.password_hash):
        raise unauthorized("Invalid email or password")
    token = create_access_token(user_id=user.id, email=user.email, role=UserRole(user.role))
    return TokenResponse(access_token=token)


@router.get("/me")
def me(user: UserRow = Depends(get_current_user)) -> UserResponse:
    return user_response(user)

