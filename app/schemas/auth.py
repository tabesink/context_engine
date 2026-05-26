from pydantic import BaseModel, Field

from app.domain.models import UserRole


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    username: str
    role: UserRole
    is_active: bool

