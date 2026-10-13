from copy import deepcopy
from uuid import uuid4
from datetime import datetime, timezone

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import create_app


class FakeUserRepository:
    def __init__(self):
        self.users = {}

    async def save(self, user):
        user.id = max(self.users, default=0) + 1
        user.create_at = user.update_at = datetime.now(timezone.utc)
        self.users[user.id] = deepcopy(user)

    async def get_by_id(self, user_id):
        return deepcopy(self.users.get(user_id))

    async def list(self, *, offset, limit):
        return deepcopy(list(self.users.values())[offset:offset + limit])

    async def update(self, user):
        user.update_at = datetime.now(timezone.utc)
        self.users[user.id] = deepcopy(user)

    async def delete(self, user):
        del self.users[user.id]


@pytest.fixture
def client():
    application = create_app(FakeUserRepository())
    with TestClient(application) as test_client:
        async def lookup(request):
            return httpx.Response(200, json={
                "cep": "01001-000", "logradouro": "Praça da Sé",
                "bairro": "Sé", "localidade": "São Paulo", "uf": "SP",
            })

        with_http = httpx.AsyncClient(transport=httpx.MockTransport(lookup))
        application.state.http_client = with_http
        yield test_client
        test_client.portal.call(with_http.aclose)


def payload():
    return {
        "primary_name": "Fernando", "secondary_name": "Silva",
        "cpf": "52998224725", "email": "fernando@example.com", "role": "client",
        "address": {"cep": "01001000", "number": "10", "complement": "Sala 1"},
    }


def test_crud(client):
    response = client.post("/users", json=payload())
    assert response.status_code == 201
    user = response.json()
    assert user["id"] == 1
    assert user["system_id"]
    assert user["create_at"] and user["update_at"]
    assert user["address"]["city"] == "São Paulo"
    assert "adress" not in user
    url = f'/users/{user["id"]}'
    public_user = {key: value for key, value in user.items() if key != "system_id"}
    assert client.get(url).json() == public_user
    assert client.get("/users").json() == [public_user]
    assert client.get("/users?offset=1&limit=1").json() == []

    response = client.patch(url, json={
        "primary_name": "Roberto", "secondary_name": "Souza", "role": "manager",
        "email": "roberto@example.com", "address": {"number": "20", "complement": None},
    })
    assert response.status_code == 200
    updated = response.json()
    assert updated["primary_name"] == "Roberto"
    assert updated["secondary_name"] == "Souza"
    assert updated["role"] == "manager"
    assert updated["email"] == "roberto@example.com"
    assert updated["address"]["number"] == "20"
    assert updated["address"]["complement"] is None
    assert updated["address"]["cep"] == "01001000"
    assert client.get(url).json() == {
        key: value for key, value in updated.items() if key != "system_id"
    }
    response = client.delete(url)
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(url).status_code == 404
    assert client.get("/users").json() == []


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_missing_user(client, method):
    kwargs = {"json": {}} if method == "patch" else {}
    assert getattr(client, method)("/users/999", **kwargs).status_code == 404


def test_invalid_input(client):
    data = payload()
    data["cpf"] = "11111111111"
    assert client.post("/users", json=data).status_code == 422
    data = payload()
    data["address"]["cep"] = "invalid"
    assert client.post("/users", json=data).status_code == 422
    assert client.get("/users/not-a-uuid").status_code == 422
    assert client.get(f"/users/{uuid4()}").status_code == 422
    assert client.get("/users/0").status_code == 422
    assert client.get("/users/-1").status_code == 422
    assert client.get("/users?limit=101").status_code == 422


@pytest.mark.parametrize("field, value", [
    ("id", 1), ("system_id", str(uuid4())),
    ("create_at", "2026-01-01T00:00:00Z"),
    ("update_at", "2026-01-01T00:00:00Z"),
])
def test_system_fields_cannot_be_supplied(client, field, value):
    data = payload()
    data[field] = value
    assert client.post("/users", json=data).status_code == 422
    created = client.post("/users", json=payload()).json()
    assert client.patch(f'/users/{created["id"]}', json={field: value}).status_code == 422


def test_default_repository_uses_database_session(monkeypatch):
    from unittest.mock import AsyncMock
    from app.shared.infrastructure.database import engine as database

    session = AsyncMock()
    session.scalars.return_value = []
    context = AsyncMock()
    context.__aenter__.return_value = session
    monkeypatch.setattr(database, "AsyncSessionLocal", lambda: context)
    with TestClient(create_app()) as client:
        response = client.get("/users")
        assert response.status_code == 200
        assert response.json() == []
    session.scalars.assert_awaited_once()
    context.__aexit__.assert_awaited_once()


@pytest.mark.parametrize("provider_status, body, expected", [
    (200, {"erro": True}, 422),
    (503, {}, 502),
])
def test_cep_provider_errors(client, provider_status, body, expected):
    async def lookup(request):
        return httpx.Response(provider_status, json=body)

    original = client.app.state.http_client
    replacement = httpx.AsyncClient(transport=httpx.MockTransport(lookup))
    client.app.state.http_client = replacement
    try:
        assert client.post("/users", json=payload()).status_code == expected
        assert client.get("/users").json() == []
    finally:
        client.portal.call(replacement.aclose)
        client.app.state.http_client = original
