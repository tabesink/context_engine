from __future__ import annotations

from app.core.config import get_settings
from app.core.security import verify_password
from app.storage.db import SessionLocal
from app.storage.repositories.users import UserRepository
from app.storage.tables import UserRow


def ensure_seed_admin(*, sync_password: bool | None = None) -> UserRow:
    """Create the configured seed admin or, in local dev, align its password with .env."""
    settings = get_settings()
    if sync_password is None:
        sync_password = settings.environment == "local"

    with SessionLocal() as session:
        repository = UserRepository(session)
        login_name = settings.seed_admin_username
        existing = repository.get_by_username(login_name)
        if existing:
            if sync_password and not verify_password(settings.seed_admin_password, existing.password_hash):
                updated = repository.reset_password(existing.id, settings.seed_admin_password)
                return updated or existing
            return existing
        return repository.ensure_admin(username=login_name, password=settings.seed_admin_password)
