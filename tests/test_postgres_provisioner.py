"""Regression tests for LightRAG Postgres provisioner DDL composition.

Verifies that CREATE ROLE / ALTER ROLE password clauses use sql.Literal
(producing a SQL string literal) rather than bind parameters ($1 / %s),
which PostgreSQL rejects in DDL context.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from psycopg import sql

from app.lightrag_deploy.postgres_provisioner import LightRAGPostgresProvisioner


# ---------------------------------------------------------------------------
# SQL composition unit tests (no live Postgres connection needed)
# ---------------------------------------------------------------------------


def test_create_role_password_uses_literal_not_bind() -> None:
    username = "lightrag_test"
    password = "pa'ss word"

    query = sql.SQL("CREATE ROLE {} WITH LOGIN PASSWORD {}").format(
        sql.Identifier(username),
        sql.Literal(password),
    )
    rendered = query.as_string()

    assert '"lightrag_test"' in rendered
    assert "$1" not in rendered
    assert "%s" not in rendered
    assert "LOGIN PASSWORD" in rendered


def test_alter_role_password_uses_literal_not_bind() -> None:
    username = "lightrag_test"
    password = "s3cret!"

    query = sql.SQL("ALTER ROLE {} WITH LOGIN PASSWORD {}").format(
        sql.Identifier(username),
        sql.Literal(password),
    )
    rendered = query.as_string()

    assert '"lightrag_test"' in rendered
    assert "$1" not in rendered
    assert "%s" not in rendered
    assert "LOGIN PASSWORD" in rendered


def test_literal_password_with_special_characters() -> None:
    password = "it's a \"complex\" p@$$w0rd"

    rendered = sql.Literal(password).as_string()

    assert "$1" not in rendered
    assert "%s" not in rendered
    assert "'" in rendered


# ---------------------------------------------------------------------------
# Input guard tests (mocked — _ensure_role never reaches psycopg.connect)
# ---------------------------------------------------------------------------

def _make_provisioner() -> LightRAGPostgresProvisioner:
    settings = MagicMock()
    settings.database_url_for_admin = "postgresql+psycopg://u:p@localhost:5432/admin"
    settings.postgres_admin_database = "postgres"
    settings.postgres_vector_extension = "vector"
    settings.postgres_age_extension = "age"
    return LightRAGPostgresProvisioner(settings)


def test_ensure_role_rejects_empty_username() -> None:
    provisioner = _make_provisioner()
    with pytest.raises(ValueError, match="username cannot be empty"):
        provisioner._ensure_role("", "password123")


def test_ensure_role_rejects_whitespace_only_username() -> None:
    provisioner = _make_provisioner()
    with pytest.raises(ValueError, match="username cannot be empty"):
        provisioner._ensure_role("   ", "password123")


def test_ensure_role_rejects_empty_password() -> None:
    provisioner = _make_provisioner()
    with pytest.raises(ValueError, match="password cannot be empty"):
        provisioner._ensure_role("lightrag_test", "")


# ---------------------------------------------------------------------------
# Integration-style test: _ensure_role composes correct SQL for CREATE path
# ---------------------------------------------------------------------------


@patch("app.lightrag_deploy.postgres_provisioner.psycopg.connect")
def test_ensure_role_create_path_sends_literal_password(mock_connect: MagicMock) -> None:
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_connect.return_value.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    mock_cur.fetchone.return_value = None  # role does not exist

    provisioner = _make_provisioner()
    provisioner._ensure_role("lightrag_test", "s3cret")

    create_call = mock_cur.execute.call_args_list[-1]
    composed_sql = create_call[0][0]
    rendered = composed_sql.as_string()

    assert "CREATE ROLE" in rendered
    assert '"lightrag_test"' in rendered
    assert "'s3cret'" in rendered
    assert "$1" not in rendered
    assert "%s" not in rendered
    assert len(create_call[0]) == 1  # no bind-parameter tuple


@patch("app.lightrag_deploy.postgres_provisioner.psycopg.connect")
def test_ensure_role_alter_path_sends_literal_password(mock_connect: MagicMock) -> None:
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_connect.return_value.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    mock_cur.fetchone.return_value = (1,)  # role already exists

    provisioner = _make_provisioner()
    provisioner._ensure_role("lightrag_test", "s3cret")

    alter_call = mock_cur.execute.call_args_list[-1]
    composed_sql = alter_call[0][0]
    rendered = composed_sql.as_string()

    assert "ALTER ROLE" in rendered
    assert '"lightrag_test"' in rendered
    assert "'s3cret'" in rendered
    assert "$1" not in rendered
    assert "%s" not in rendered
    assert len(alter_call[0]) == 1  # no bind-parameter tuple


@patch("app.lightrag_deploy.postgres_provisioner.psycopg.connect")
def test_ensure_extensions_configures_age_for_lightrag_sessions(
    mock_connect: MagicMock,
) -> None:
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_connect.return_value.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    statuses = _make_provisioner()._ensure_extensions("lightrag_test")

    rendered = [
        call.args[0].as_string() if hasattr(call.args[0], "as_string") else call.args[0]
        for call in mock_cur.execute.call_args_list
    ]
    assert statuses["age"].status == "ok"
    assert 'CREATE EXTENSION IF NOT EXISTS "age" CASCADE' in rendered
    assert (
        'ALTER DATABASE "lightrag_test" SET session_preload_libraries = \'age\''
        in rendered
    )
    assert (
        # Keep public first so LightRAG creates unqualified app tables outside ag_catalog.
        'ALTER DATABASE "lightrag_test" SET search_path = public, ag_catalog, "$user"'
        in rendered
    )


@patch("app.lightrag_deploy.postgres_provisioner.psycopg.connect")
def test_grant_database_privileges_grants_age_schema_when_present(
    mock_connect: MagicMock,
) -> None:
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_connect.return_value.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    mock_cur.fetchone.return_value = (1,)

    _make_provisioner()._grant_database_privileges("lightrag_test", "lightrag_test")

    rendered = [
        call.args[0].as_string() if hasattr(call.args[0], "as_string") else call.args[0]
        for call in mock_cur.execute.call_args_list
    ]
    assert 'GRANT USAGE ON SCHEMA ag_catalog TO "lightrag_test"' in rendered
    assert 'GRANT SELECT ON TABLE ag_catalog.ag_graph TO "lightrag_test"' in rendered
