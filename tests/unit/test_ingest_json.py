import json

import httpx
import pytest

from app.bootstrap.ingest_json import IngestionError, ingest, load_records, main


def test_posts_to_corresponding_endpoints_and_remaps_generated_ids():
    requests = []

    def handler(request):
        requests.append((request.url.path, json.loads(request.content)))
        body = {"id": 91} if request.url.path == "/users" else {"vehicle_id": 72}
        return httpx.Response(201, json=body)

    records = {
        "users": [{"primary_name": "Ana"}],
        "stock": [{"tool_name": "Chave"}],
        "vehicles": [{"owner_id": 1}],
        "budgets": [{"technical_id": 1, "client_id": 1, "vehicle_id": 1}],
    }
    with httpx.Client(base_url="http://test/", transport=httpx.MockTransport(handler)) as client:
        assert ingest(client, records) == 4
    assert [path for path, _ in requests] == ["/users", "/stock", "/vehicles", "/budgets"]
    assert requests[2][1]["owner_id"] == 91
    assert requests[3][1] == {"technical_id": 91, "client_id": 91, "vehicle_id": 72}
    assert records["vehicles"][0]["owner_id"] == 1


def test_http_failure_stops_without_retry_or_exposing_response():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(409, json={"detail": "private data"})

    with httpx.Client(base_url="http://test/", transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(IngestionError, match="HTTP 409") as error:
            ingest(client, {"stock": [{}, {}]})
    assert len(calls) == 1
    assert "private data" not in str(error.value)


def test_validation_reports_file_record_and_field_without_input(tmp_path):
    (tmp_path / "users.json").write_text('[{"cpf": "private data"}]', encoding="utf-8")
    with pytest.raises(IngestionError, match="users.json, registro 1, cpf") as error:
        load_records(tmp_path, ["users"])
    assert "private data" not in str(error.value)


def test_dry_run_does_not_create_http_client(tmp_path, monkeypatch):
    payload = {
        "tool_name": "Chave", "quantity": 2, "price": 10, "batch": "A",
        "replacement_time_hours": 24, "replacement_time_days": 1,
    }
    (tmp_path / "stock.json").write_text(json.dumps([payload]), encoding="utf-8")

    def forbidden_client(*args, **kwargs):
        pytest.fail("dry-run não deve abrir um cliente HTTP")

    monkeypatch.setattr(httpx, "Client", forbidden_client)
    assert main(["--data-dir", str(tmp_path), "--resources", "stock", "--dry-run"]) == 0


def test_invalid_json_returns_failure(tmp_path):
    (tmp_path / "stock.json").write_text("{", encoding="utf-8")
    assert main(["--data-dir", str(tmp_path), "--resources", "stock", "--dry-run"]) == 1


def test_import_preserves_password_instead_of_secretstr_mask(tmp_path):
    from test_users_router import payload

    data = payload()
    (tmp_path / "users.json").write_text(json.dumps([data]), encoding="utf-8")
    records = load_records(tmp_path, ["users"])
    assert records["users"][0]["password"] == data["password"]


def test_initial_password_only_applies_to_users_without_password(tmp_path):
    from test_users_router import payload

    explicit = payload()
    without_password = {key: value for key, value in explicit.items() if key != "password"}
    (tmp_path / "users.json").write_text(json.dumps([explicit, without_password]), encoding="utf-8")
    records = load_records(tmp_path, ["users"], user_password="initial-password-123")
    assert records["users"][0]["password"] == explicit["password"]
    assert records["users"][1]["password"] == "initial-password-123"
