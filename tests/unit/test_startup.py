from unittest.mock import MagicMock

import httpx
import pytest

from app.bootstrap import start_server
from app.bootstrap.ingest_json import IngestionError, load_records
from app.bootstrap.seed_initial_data import import_records


def test_startup_order_and_test_failure_blocks_ingestion(monkeypatch):
    import subprocess

    calls = []

    def run(command, **kwargs):
        calls.append(command)
        if "pytest" in command:
            raise subprocess.CalledProcessError(1, command)

    start = MagicMock()
    monkeypatch.setattr(start_server.subprocess, "run", run)
    monkeypatch.setattr(start_server.os, "execvp", start)
    with pytest.raises(subprocess.CalledProcessError):
        start_server.main()
    assert [command[2] for command in calls] == [
        "app.bootstrap.create_tables", "app.bootstrap.migrate_notification_type", "pytest",
    ]
    start.assert_not_called()


def test_successful_startup_runs_tests_then_seed_then_server(monkeypatch):
    run = MagicMock()
    start = MagicMock()
    monkeypatch.setattr(start_server.subprocess, "run", run)
    monkeypatch.setattr(start_server.os, "execvp", start)
    start_server.main()
    assert [call.args[0][2] for call in run.call_args_list] == [
        "app.bootstrap.create_tables", "app.bootstrap.migrate_notification_type", "pytest",
        "app.bootstrap.seed_initial_data",
    ]
    start.assert_called_once()


async def test_initial_import_remaps_relations():
    requests = []

    def handler(request):
        import json

        requests.append((request.url.path, json.loads(request.content)))
        return httpx.Response(201, json={"id": 91, "vehicle_id": 72, "tool_id": "stock-uuid"})

    records = {
        "users": [{"primary_name": "Ana"}], "stock": [{"tool_name": "Chave"}],
        "vehicles": [{"owner_id": 1}],
        "budgets": [{"technical_id": 1, "client_id": 1, "vehicle_id": 1,
                     "tools": [{"tool_id": "__seed_stock_position__:1", "tool_name": "Chave", "quantity": 1}]}],
    }
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://test") as client:
        assert await import_records(client, records) == 4
    assert [path for path, _ in requests] == ["/users", "/stock", "/vehicles", "/budgets"]
    assert requests[-1][1] == {
        "technical_id": 91, "client_id": 91, "vehicle_id": 72,
        "tools": [{"tool_id": "stock-uuid", "tool_name": "Chave", "quantity": 1}],
    }
    assert records["vehicles"][0]["owner_id"] == 1


async def test_initial_import_stops_without_leaking_error_body():
    def handler(request):
        return httpx.Response(409, json={"detail": "sensitive data"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://test") as client:
        with pytest.raises(IngestionError, match="HTTP 409") as error:
            await import_records(client, {"users": [{}]})
    assert "sensitive data" not in str(error.value)


@pytest.mark.parametrize("stock_count", [0, 1, 2])
def test_initial_load_requires_unique_stock_name(tmp_path, stock_count):
    import json

    stock = {
        "tool_name": "Chave", "quantity": 1, "price": 10, "batch": "A",
        "replacement_time_hours": 1, "replacement_time_days": 1,
    }
    budget = {
        "technical_id": 1, "client_id": 2, "vehicle_id": 1, "technical_name": "Técnico",
        "technical_disponibility": True, "service_name": "Revisão", "amount": 10,
        "duration_service_hours": 1, "duration_service_days": 1,
        "tools": [{"tool_name": "Chave", "quantity": 1}],
    }
    (tmp_path / "stock.json").write_text(json.dumps([stock] * stock_count), encoding="utf-8")
    (tmp_path / "budgets.json").write_text(json.dumps([budget]), encoding="utf-8")
    if stock_count == 1:
        records = load_records(tmp_path, ["stock", "budgets"], resolve_stock_names=True)
        assert records["budgets"][0]["tools"][0]["tool_id"] == "__seed_stock_position__:1"
    else:
        with pytest.raises(IngestionError, match="correspondência única"):
            load_records(tmp_path, ["stock", "budgets"], resolve_stock_names=True)
