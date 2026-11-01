import sqlite3
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.main import create_app
from app.shared.infrastructure.database.integrity_errors import integrity_error_details


@pytest.mark.parametrize("sqlstate, expected_code", [
    ("23505", "unique_violation"),
    ("23503", "foreign_key_violation"),
    ("23502", "not_null_violation"),
    ("23514", "check_violation"),
    ("23P01", "exclusion_violation"),
])
def test_postgres_driver_metadata(sqlstate, expected_code):
    original = Exception("private database message")
    original.sqlstate = sqlstate
    original.table_name = "vehicles"
    original.constraint_name = "vehicles_owner_id_fkey"
    original.detail = "Key (owner_id)=(123) is not present in table users."
    adapter = Exception("asyncpg adapter")
    adapter.__cause__ = original
    result = integrity_error_details(IntegrityError("INSERT ...", {"secret": "value"}, adapter))

    assert result["error"] == {
        "code": expected_code,
        "fields": ["owner_id"],
        "table": "vehicles",
        "constraint": "vehicles_owner_id_fkey",
    }
    assert "123" not in str(result)
    assert "private" not in str(result)
    assert "secret" not in str(result)


def test_psycopg_diagnostics_and_composite_fields():
    original = Exception()
    original.pgcode = "23505"
    original.diag = SimpleNamespace(
        table_name="vehicles", constraint_name="unique_vehicle",
        message_detail='Key (brand, model)=(private, private) already exists.',
    )
    result = integrity_error_details(IntegrityError(None, None, original))
    assert result["error"]["fields"] == ["brand", "model"]
    assert result["error"]["constraint"] == "unique_vehicle"


def test_not_null_uses_column_metadata():
    original = Exception()
    original.sqlstate = "23502"
    original.column_name = "owner_id"
    result = integrity_error_details(IntegrityError(None, None, original))
    assert result["error"]["fields"] == ["owner_id"]


def test_sqlite_unique_violation():
    with sqlite3.connect(":memory:") as connection:
        connection.execute("CREATE TABLE users (cpf TEXT UNIQUE)")
        connection.execute("INSERT INTO users VALUES ('private')")
        with pytest.raises(sqlite3.IntegrityError) as captured:
            connection.execute("INSERT INTO users VALUES ('private')")
    result = integrity_error_details(IntegrityError(None, None, captured.value))
    assert result["error"]["code"] == "unique_violation"
    assert result["error"]["fields"] == ["cpf"]


def test_http_conflict_response():
    application = create_app()

    @application.get("/test-integrity-conflict")
    def conflict():
        original = Exception("private database message")
        original.sqlstate = "23505"
        original.detail = "Key (cpf)=(private) already exists."
        raise IntegrityError("INSERT INTO users ...", {"cpf": "private"}, original)

    with TestClient(application) as client:
        response = client.get("/test-integrity-conflict")
    assert response.status_code == 409
    assert isinstance(response.json()["detail"], str)
    assert response.json()["error"]["code"] == "unique_violation"
    assert response.json()["error"]["fields"] == ["cpf"]
    assert "private" not in response.text
    assert "INSERT" not in response.text


def test_unknown_integrity_error_keeps_generic_response():
    result = integrity_error_details(IntegrityError("private SQL", None, Exception("private")))
    assert result["error"] == {
        "code": "integrity_conflict", "fields": [], "table": None, "constraint": None,
    }
    assert "private" not in str(result)
