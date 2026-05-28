from app.core.config import get_settings
from app.core.security import verify_password
from app.domain.models import UserRole
from app.seed import ensure_seed_admin
from app.storage.db import SessionLocal, create_db_and_tables
from app.storage.repositories.users import UserRepository


def test_ensure_seed_admin_syncs_local_password() -> None:
    create_db_and_tables()
    settings = get_settings()
    login_name = settings.seed_admin_username

    with SessionLocal() as session:
        repository = UserRepository(session)
        existing = repository.get_by_username(login_name)
        if existing:
            repository.reset_password(existing.id, "stale-password")
        else:
            repository.create(username=login_name, password="stale-password", role=UserRole.ADMIN)

    user = ensure_seed_admin(sync_password=True)
    assert verify_password(settings.seed_admin_password, user.password_hash)
    assert not verify_password("stale-password", user.password_hash)
