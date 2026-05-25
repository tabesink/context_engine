from app.core.config import get_settings
from app.storage.db import SessionLocal, create_db_and_tables
from app.storage.repositories.users import UserRepository


def main() -> None:
    settings = get_settings()
    create_db_and_tables()
    with SessionLocal() as session:
        user = UserRepository(session).ensure_admin(
            username=settings.seed_admin_username,
            password=settings.seed_admin_password,
        )
        print(f"Seed admin ready: {user.email}")


if __name__ == "__main__":
    main()

