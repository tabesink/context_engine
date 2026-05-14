from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def _engine_url() -> str:
    settings = get_settings()
    if settings.database_url.startswith("sqlite"):
        Path(".data").mkdir(parents=True, exist_ok=True)
    return settings.database_url


engine = create_engine(_engine_url(), future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def create_db_and_tables() -> None:
    from app.storage import tables  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

