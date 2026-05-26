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

    def list_all(self) -> list[UserRow]:
        return list(self.session.scalars(select(UserRow).order_by(UserRow.created_at.asc(), UserRow.email.asc())).all())

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

    def update_role(self, user_id: str, role: UserRole) -> UserRow | None:
        user = self.get_by_id(user_id)
        if not user:
            return None
        user.role = role.value
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def reset_password(self, user_id: str, new_password: str) -> UserRow | None:
        user = self.get_by_id(user_id)
        if not user:
            return None
        user.password_hash = hash_password(new_password)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def delete(self, user_id: str) -> bool:
        user = self.get_by_id(user_id)
        if not user:
            return False
        self.session.delete(user)
        self.session.commit()
        return True

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

