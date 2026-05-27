import asyncio
import ast
from pathlib import Path
from types import SimpleNamespace


POSTGRES_IMPL = Path(__file__).resolve().parents[1] / "external/lightrag/kg/postgres_impl.py"


class InvalidSchemaNameError(Exception):
    pass


class UniqueViolationError(Exception):
    pass


asyncpg = SimpleNamespace(
    Connection=object,
    exceptions=SimpleNamespace(
        InvalidSchemaNameError=InvalidSchemaNameError,
        UniqueViolationError=UniqueViolationError,
    )
)


def _load_postgresql_db_configure_age_class():
    tree = ast.parse(POSTGRES_IMPL.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "PostgreSQLDB":
            for item in node.body:
                if isinstance(item, ast.AsyncFunctionDef) and item.name == "configure_age":
                    class_def = ast.ClassDef(
                        name=node.name,
                        bases=[],
                        keywords=[],
                        body=[item],
                        decorator_list=[],
                    )
                    module = ast.Module(
                        body=[class_def],
                        type_ignores=[],
                    )
                    ast.fix_missing_locations(module)
                    namespace = {"asyncpg": asyncpg, "staticmethod": staticmethod}
                    exec(compile(module, str(POSTGRES_IMPL), "exec"), namespace)
                    return namespace[node.name]
    raise AssertionError("PostgreSQLDB.configure_age not found")


PostgreSQLDB = _load_postgresql_db_configure_age_class()


class FakeAgeConnection:
    def __init__(self, *, graph_exists: bool) -> None:
        self.graph_exists = graph_exists
        self.calls: list[tuple[str, str, tuple[object, ...]]] = []

    async def execute(self, sql: str, *args: object) -> str:
        self.calls.append(("execute", sql, args))
        return "OK"

    async def fetchval(self, sql: str, *args: object) -> bool:
        self.calls.append(("fetchval", sql, args))
        return self.graph_exists


def test_configure_age_does_not_create_existing_graph() -> None:
    connection = FakeAgeConnection(graph_exists=True)

    asyncio.run(PostgreSQLDB.configure_age(connection, "test4_chunk_entity_relation"))

    assert connection.calls == [
        ("execute", 'SET search_path = ag_catalog, "$user", public', ()),
        (
            "fetchval",
            "SELECT EXISTS(SELECT 1 FROM ag_catalog.ag_graph WHERE name = $1)",
            ("test4_chunk_entity_relation",),
        ),
    ]


def test_configure_age_creates_missing_graph() -> None:
    connection = FakeAgeConnection(graph_exists=False)

    asyncio.run(PostgreSQLDB.configure_age(connection, "test4_chunk_entity_relation"))

    assert connection.calls == [
        ("execute", 'SET search_path = ag_catalog, "$user", public', ()),
        (
            "fetchval",
            "SELECT EXISTS(SELECT 1 FROM ag_catalog.ag_graph WHERE name = $1)",
            ("test4_chunk_entity_relation",),
        ),
        ("execute", "SELECT create_graph($1)", ("test4_chunk_entity_relation",)),
    ]
