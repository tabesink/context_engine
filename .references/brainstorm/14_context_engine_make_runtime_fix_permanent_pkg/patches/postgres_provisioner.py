"""Postgres provisioning for managed LightRAG domains.

Implementation skeleton. Wire this into LightRAGDomainService before env generation
and before Docker compose up/recreate.

This code assumes psycopg v3 is available through the project dependencies.
If not, implement the same logic with SQLAlchemy using AUTOCOMMIT for CREATE DATABASE.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import quote_plus

import psycopg
from psycopg import sql

from app.lightrag_deploy.models import LightRAGDomain
from app.lightrag_deploy.settings import LightRAGDeploySettings


@dataclass(frozen=True)
class LightRAGPostgresTarget:
    database: str
    user: str
    password: str


@dataclass(frozen=True)
class LightRAGPostgresProvisionResult:
    database: str
    user: str
    role_created: bool = False
    database_created: bool = False
    vector_extension_enabled: bool = False
    age_extension_enabled: bool = False
    warnings: list[str] = field(default_factory=list)


class LightRAGPostgresProvisioner:
    def __init__(self, settings: LightRAGDeploySettings):
        self.settings = settings

    def target_for_domain(self, domain: LightRAGDomain) -> LightRAGPostgresTarget:
        mode = self.settings.postgres_provisioning_mode

        if mode == "compat":
            return LightRAGPostgresTarget(
                database=self.settings.postgres_compat_database,
                user=self.settings.postgres_compat_user,
                password=self.settings.postgres_compat_password,
            )

        if mode == "app_database_shared":
            return LightRAGPostgresTarget(
                database=self.settings.runtime_postgres_database,
                user=self.settings.runtime_postgres_user,
                password=self.settings.runtime_postgres_password,
            )

        # default: per_domain
        if not domain.postgres_database or not domain.postgres_user:
            raise ValueError(f"Domain {domain.id!r} does not define Postgres database/user")
        return LightRAGPostgresTarget(
            database=domain.postgres_database,
            user=domain.postgres_user,
            password=self.settings.postgres_password,
        )

    def ensure_for_domain(self, domain: LightRAGDomain) -> LightRAGPostgresProvisionResult:
        return self.ensure_target(self.target_for_domain(domain))

    def ensure_legacy_compat(self) -> LightRAGPostgresProvisionResult | None:
        if not self.settings.postgres_compat_enabled:
            return None
        return self.ensure_target(
            LightRAGPostgresTarget(
                database=self.settings.postgres_compat_database,
                user=self.settings.postgres_compat_user,
                password=self.settings.postgres_compat_password,
            )
        )

    def ensure_target(self, target: LightRAGPostgresTarget) -> LightRAGPostgresProvisionResult:
        role_created = self._ensure_role(target.user, target.password)
        database_created = self._ensure_database(target.database, target.user)
        self._grant_database_privileges(target.database, target.user)
        vector_ok, age_ok, warnings = self._ensure_extensions(target.database)
        return LightRAGPostgresProvisionResult(
            database=target.database,
            user=target.user,
            role_created=role_created,
            database_created=database_created,
            vector_extension_enabled=vector_ok,
            age_extension_enabled=age_ok,
            warnings=warnings,
        )

    def _admin_conninfo(self, *, database: str | None = None) -> str:
        # Prefer the same in-network Postgres service used by Compose.
        db = database or self.settings.runtime_postgres_database or "context_engine"
        return (
            f"host={self.settings.postgres_host} "
            f"port={self.settings.postgres_port} "
            f"dbname={db} "
            f"user={self.settings.runtime_postgres_user} "
            f"password={self.settings.runtime_postgres_password}"
        )

    def _ensure_role(self, user: str, password: str) -> bool:
        with psycopg.connect(self._admin_conninfo(), autocommit=True) as conn:
            exists = conn.execute(
                "SELECT 1 FROM pg_roles WHERE rolname = %s",
                (user,),
            ).fetchone()
            if exists:
                # Keep password aligned with current .env so repair really repairs.
                conn.execute(
                    sql.SQL("ALTER ROLE {} LOGIN PASSWORD %s").format(sql.Identifier(user)),
                    (password,),
                )
                return False
            conn.execute(
                sql.SQL("CREATE ROLE {} LOGIN PASSWORD %s").format(sql.Identifier(user)),
                (password,),
            )
            return True

    def _ensure_database(self, database: str, owner: str) -> bool:
        with psycopg.connect(self._admin_conninfo(), autocommit=True) as conn:
            exists = conn.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (database,),
            ).fetchone()
            if exists:
                conn.execute(
                    sql.SQL("ALTER DATABASE {} OWNER TO {}").format(
                        sql.Identifier(database),
                        sql.Identifier(owner),
                    )
                )
                return False
            conn.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(database),
                    sql.Identifier(owner),
                )
            )
            return True

    def _grant_database_privileges(self, database: str, user: str) -> None:
        with psycopg.connect(self._admin_conninfo(database=database), autocommit=True) as conn:
            conn.execute(
                sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                    sql.Identifier(database),
                    sql.Identifier(user),
                )
            )
            conn.execute(sql.SQL("GRANT USAGE, CREATE ON SCHEMA public TO {}").format(sql.Identifier(user)))
            conn.execute(sql.SQL("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {}").format(sql.Identifier(user)))
            conn.execute(sql.SQL("GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO {}").format(sql.Identifier(user)))
            conn.execute(sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {}").format(sql.Identifier(user)))
            conn.execute(sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO {}").format(sql.Identifier(user)))

    def _ensure_extensions(self, database: str) -> tuple[bool, bool, list[str]]:
        warnings: list[str] = []
        vector_ok = False
        age_ok = False
        with psycopg.connect(self._admin_conninfo(database=database), autocommit=True) as conn:
            try:
                conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                vector_ok = True
            except Exception as exc:
                warnings.append(f"Failed to enable vector extension in {database}: {exc}")

            try:
                conn.execute("CREATE EXTENSION IF NOT EXISTS age CASCADE")
                age_ok = True
            except Exception as exc:
                warnings.append(f"AGE extension not enabled in {database}: {exc}")

        if not vector_ok:
            raise RuntimeError(f"vector extension is required for LightRAG PGVectorStorage in {database}")

        return vector_ok, age_ok, warnings
