from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.errors import forbidden, unauthorized
from app.core.security import decode_access_token
from app.domain.models import UserRole
from app.storage.db import get_session
from app.storage.repositories.users import UserRepository
from app.storage.tables import UserRow

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> UserRow:
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise unauthorized("Invalid authentication token")
    user = UserRepository(session).get_by_id(user_id)
    if not user or not user.is_active:
        raise unauthorized("User is inactive or missing")
    return user


def require_admin(user: UserRow = Depends(get_current_user)) -> UserRow:
    if user.role != UserRole.ADMIN.value:
        raise forbidden("Admin access required")
    return user

