from dataclasses import dataclass, field
from urllib.parse import urlparse, urlunparse

import psycopg
from psycopg import sql

from app.lightrag_deploy.models import LightRAGDomain
from app.lightrag_deploy.settings import LightRAGDeploySettings


@dataclass(frozen=True)
class PostgresExtensionStatus:
    name: str
    status: str
    message: str | None = None


@dataclass(frozen=True)
class LightRAGPostgresProvisionResult:
    database: str
    user: str
    role_exists: bool
    database_exists: bool
    extensions: dict[str, PostgresExtensionStatus] = field(default_factory=dict)


class LightRAGPostgresProvisioner:
    def __init__(self, settings: LightRAGDeploySettings):
        self.settings = settings
        self.admin_dsn = _psycopg_dsn(settings.database_url_for_admin)

    def provision_domain(self, domain: LightRAGDomain) -> LightRAGPostgresProvisionResult:
        if not domain.postgres_database or not domain.postgres_user:
            raise ValueError(
                f"LightRAG domain {domain.id!r} is missing postgres_database/postgres_user"
            )
        if not self.settings.postgres_password:
            raise ValueError("LIGHTRAG_POSTGRES_PASSWORD must be set for postgres storage")

        self._ensure_role(domain.postgres_user, self.settings.postgres_password)
        self._ensure_database(domain.postgres_database, domain.postgres_user)
        self._grant_database_privileges(domain.postgres_database, domain.postgres_user)
        extensions = self._ensure_extensions(domain.postgres_database)

        return LightRAGPostgresProvisionResult(
            database=domain.postgres_database,
            user=domain.postgres_user,
            role_exists=self.role_exists(domain.postgres_user),
            database_exists=self.database_exists(domain.postgres_database),
            extensions=extensions,
        )

    def role_exists(self, username: str) -> bool:
        with psycopg.connect(self.admin_dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (username,))
                return cur.fetchone() is not None

    def database_exists(self, database: str) -> bool:
        with psycopg.connect(self.admin_dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database,))
                return cur.fetchone() is not None

    def _ensure_role(self, username: str, password: str) -> None:
        with psycopg.connect(self.admin_dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (username,))
                role_exists = cur.fetchone() is not None
                if role_exists:
                    cur.execute(
                        sql.SQL("ALTER ROLE {} WITH LOGIN PASSWORD %s").format(
                            sql.Identifier(username)
                        ),
                        (password,),
                    )
                    return
                cur.execute(
                    sql.SQL("CREATE ROLE {} LOGIN PASSWORD %s").format(sql.Identifier(username)),
                    (password,),
                )

    def _ensure_database(self, database: str, owner: str) -> None:
        with psycopg.connect(self.admin_dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database,))
                database_exists = cur.fetchone() is not None
                if database_exists:
                    cur.execute(
                        sql.SQL("ALTER DATABASE {} OWNER TO {}").format(
                            sql.Identifier(database),
                            sql.Identifier(owner),
                        )
                    )
                    return
                cur.execute(
                    sql.SQL("CREATE DATABASE {} OWNER {}").format(
                        sql.Identifier(database),
                        sql.Identifier(owner),
                    )
                )

    def _grant_database_privileges(self, database: str, username: str) -> None:
        with psycopg.connect(self.admin_dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                        sql.Identifier(database),
                        sql.Identifier(username),
                    )
                )

        db_dsn = _dsn_with_database(self.admin_dsn, database)
        with psycopg.connect(db_dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("GRANT USAGE, CREATE ON SCHEMA public TO {}").format(
                        sql.Identifier(username)
                    )
                )
                cur.execute(
                    sql.SQL(
                        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {}"
                    ).format(sql.Identifier(username))
                )
                cur.execute(
                    sql.SQL(
                        "GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO {}"
                    ).format(sql.Identifier(username))
                )

    def _ensure_extensions(self, database: str) -> dict[str, PostgresExtensionStatus]:
        db_dsn = _dsn_with_database(self.admin_dsn, database)
        statuses: dict[str, PostgresExtensionStatus] = {}
        with psycopg.connect(db_dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                for extension in ("vector", "age"):
                    try:
                        cur.execute(
                            sql.SQL("CREATE EXTENSION IF NOT EXISTS {}").format(
                                sql.Identifier(extension)
                            )
                        )
                    except Exception as exc:  # pragma: no cover - image-dependent
                        statuses[extension] = PostgresExtensionStatus(
                            name=extension,
                            status="unavailable",
                            message=str(exc),
                        )
                    else:
                        statuses[extension] = PostgresExtensionStatus(
                            name=extension,
                            status="ok",
                        )
        return statuses


def _psycopg_dsn(url: str) -> str:
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


def _dsn_with_database(dsn: str, database: str) -> str:
    parsed = urlparse(dsn)
    return urlunparse(parsed._replace(path=f"/{database}"))
