from pydantic import BaseModel, Field

from app.domain.models import UserRole


class AdminUserResponse(BaseModel):
    id: str
    username: str
    role: UserRole
    is_active: bool
    created_at: str | None = None


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=128)
    password: str = Field(min_length=8, max_length=256)
    role: UserRole


class UpdateUserRequest(BaseModel):
    role: UserRole


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=256)
