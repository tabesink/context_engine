from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.domain.models import UserRole
from app.storage.tables import UserRow


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_email(self, email: str) -> UserRow | None:
        return self.session.scalar(select(UserRow).where(UserRow.email == email.lower()))

    def get_by_id(self, user_id: str) -> UserRow | None:
        return self.session.get(UserRow, user_id)

    def create(self, *, email: str, password: str, role: UserRole) -> UserRow:
        user = UserRow(
            email=email.lower(),
            password_hash=hash_password(password),
            role=role.value,
            is_active=True,
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def ensure_admin(self, *, email: str, password: str) -> UserRow:
        existing = self.get_by_email(email)
        if existing:
            return existing
        return self.create(email=email, password=password, role=UserRole.ADMIN)

