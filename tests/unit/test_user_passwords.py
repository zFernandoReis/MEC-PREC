import httpx
import pytest
from sqlalchemy import inspect

from test_security import PASSWORD, auth_client, headers, login
from test_users_router import client, payload

from app.modules.users.infrastructure.models.users_model import UserModel
from app.shared.infrastructure.security.passwords import verify_password


@pytest.mark.parametrize("password", [None, "short", "x" * 129])
def test_user_registration_requires_valid_password(client, password):
    data = payload()
    if password is None:
        data.pop("password")
    else:
        data["password"] = password
    response = client.post("/users", json=data)
    assert response.status_code == 422
    assert "input" not in response.text


def test_registration_only_persists_hash_and_profile_update_preserves_it(client):
    data = payload()
    response = client.post("/users", json=data)
    assert response.status_code == 201
    user_id = response.json()["id"]
    stored = client.app.state.user_repository.users[user_id]
    assert stored.password_hash.startswith("$argon2id$")
    assert stored.password_hash != data["password"]
    assert verify_password(data["password"], stored.password_hash)
    assert "password" not in response.text
    assert stored.password_hash not in repr(stored)
    before = stored.password_hash
    assert client.patch(f"/users/{user_id}", json={"primary_name": "Carlos"}).status_code == 200
    assert client.app.state.user_repository.users[user_id].password_hash == before
    for field in ("password", "password_hash", "token_version"):
        value = 1 if field == "token_version" else "another-secure-password"
        invalid = client.patch(f"/users/{user_id}", json={field: value})
        assert invalid.status_code == 422
        assert all("input" not in error for error in invalid.json()["detail"])
        assert "another-secure-password" not in invalid.text


def test_created_user_can_login_with_original_password(auth_client):
    client, session = auth_client
    admin = login(client).json()
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={
        "cep": "01001-000", "logradouro": "Praça da Sé", "bairro": "Sé",
        "localidade": "São Paulo", "uf": "SP",
    }))
    replacement = httpx.AsyncClient(transport=transport)
    original = client.app.state.http_client
    client.app.state.http_client = replacement
    try:
        response = client.post("/users", headers=headers(admin), json={
            "primary_name": "Carlos", "secondary_name": "Souza",
            "cpf": "12345678909", "email": "carlos@example.com", "role": "client",
            "password": PASSWORD, "address": {"cep": "01001000", "number": "1"},
        })
    finally:
        client.app.state.http_client = original
        client.portal.call(replacement.aclose)
    assert response.status_code == 201, response.text
    user_id = response.json()["id"]
    stored = session.get(UserModel, user_id)
    assert verify_password(PASSWORD, stored.password_hash)
    assert "password" not in response.json()
    assert "password_hash" not in response.json()
    assert "user_credentials" not in inspect(session.bind).get_table_names()
    result = login(client, cpf="12345678909")
    assert result.status_code == 200, result.text
    pair = result.json()
    assert client.get("/auth/me", headers=headers(pair)).json()["id"] == user_id
    previous_hash = session.get(UserModel, user_id).password_hash
    assert client.patch(f"/users/{user_id}", headers=headers(admin), json={"primary_name": "Roberto"}).status_code == 200
    assert session.get(UserModel, user_id).password_hash == previous_hash
    assert client.get("/auth/me", headers=headers(pair)).status_code == 200
