from pydantic import BaseModel, Field, model_validator

from app.domain.models import UserRole


class LoginRequest(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=128)
    email: str | None = Field(default=None, exclude=True)
    password: str

    @model_validator(mode="after")
    def normalize_legacy_email(self) -> "LoginRequest":
        if self.username is None and self.email:
            self.username = self.email
        if self.username is None:
            raise ValueError("username is required")
        return self


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    username: str
    role: UserRole
    is_active: bool

