from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.domain.models import UserRole
from app.schemas.users import (
    AdminUserResponse,
    CreateUserRequest,
    ResetPasswordRequest,
    UpdateUserRequest,
)
from app.storage.db import get_session
from app.storage.repositories.users import UserRepository
from app.storage.tables import UserRow

router = APIRouter(prefix="/admin/users", tags=["users"])


def _to_admin_user_response(user: UserRow) -> AdminUserResponse:
    created_at = user.created_at.isoformat() if user.created_at else None
    return AdminUserResponse(
        id=user.id,
        username=user.email,
        role=UserRole(user.role),
        is_active=user.is_active,
        created_at=created_at,
    )


@router.get("", response_model=list[AdminUserResponse])
def list_users(
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> list[AdminUserResponse]:
    del admin
    users = UserRepository(session).list_all()
    return [_to_admin_user_response(user) for user in users]


@router.post("", response_model=AdminUserResponse)
def create_user(
    request: CreateUserRequest,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> AdminUserResponse:
    del admin
    repository = UserRepository(session)
    username = request.username.strip().lower()
    existing = repository.get_by_username(username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User '{username}' already exists",
        )
    created = repository.create(username=username, password=request.password, role=request.role)
    return _to_admin_user_response(created)


@router.patch("/{user_id}", response_model=AdminUserResponse)
def update_user(
    user_id: str,
    request: UpdateUserRequest,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> AdminUserResponse:
    repository = UserRepository(session)
    if admin.id == user_id and request.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove your own admin role",
        )
    updated = repository.update_role(user_id, request.role)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _to_admin_user_response(updated)


@router.post("/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_user_password(
    user_id: str,
    request: ResetPasswordRequest,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> None:
    del admin
    updated = UserRepository(session).reset_password(user_id, request.new_password)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return None


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> None:
    if admin.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account",
        )
    deleted = UserRepository(session).delete(user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return None
