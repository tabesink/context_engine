from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.domain.models import UserRole
from app.storage.tables import UserRow


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_username(self, username: str) -> UserRow | None:
        return self.session.scalar(select(UserRow).where(UserRow.email == username.lower()))

    def get_by_email(self, email: str) -> UserRow | None:
        return self.get_by_username(email)

    def get_by_id(self, user_id: str) -> UserRow | None:
        return self.session.get(UserRow, user_id)

    def create(
        self,
        *,
        username: str | None = None,
        email: str | None = None,
        password: str,
        role: UserRole,
    ) -> UserRow:
        login_name = username or email
        if not login_name:
            raise ValueError("username is required")
        user = UserRow(
            email=login_name.lower(),
            password_hash=hash_password(password),
            role=role.value,
            is_active=True,
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def ensure_admin(
        self,
        *,
        username: str | None = None,
        email: str | None = None,
        password: str,
    ) -> UserRow:
        login_name = username or email
        if not login_name:
            raise ValueError("username is required")
        existing = self.get_by_username(login_name)
        if existing:
            return existing
        return self.create(username=login_name, password=password, role=UserRole.ADMIN)

