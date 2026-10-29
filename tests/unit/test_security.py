from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import jwt
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.main import create_app
from app.modules.users.domain.enums.user_role import UserRole
from app.modules.users.infrastructure.models.users_model import UserModel
from app.modules.users.infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.shared.infrastructure.security.passwords import hash_password, verify_password
from app.shared.infrastructure.security.repository import SQLAlchemyCredentialRepository
from app.shared.infrastructure.security.tokens import TokenManager

PASSWORD = "a-secure-password-123"
NEW_PASSWORD = "a-new-secure-password-456"
KEY = "test-only-secret-key-with-at-least-32-characters"
CPF = "52998224725"


@pytest.fixture
def orders_repository(auth_client):
    from app.modules.orders.application.ports.order_repository import OrderRepository
    from app.modules.orders.domain.entities.orders import Order
    from app.modules.orders.domain.enums.order_status import OrderStatus

    client, _ = auth_client
    repository = AsyncMock(spec=OrderRepository)
    repository.get_by_id.return_value = Order(
        order_id=7, client_id=2, client_email="client@example.com",
        technical_id=1, technical_name="Equipe", technical_email="team@example.com",
        technical_responser_id=1, technical_responser_name="Equipe",
        technical_responser_email="team@example.com", budget_id=4, vehicle_id=5,
        service_name="Revisão", duration_service_hours=24, duration_service_days=1,
        order_status=OrderStatus.RECEBIDA,
    )
    client.app.state.order_repository = repository
    return repository


def order_payload(repository, method):
    from app.modules.orders.application.dtos.order_dto import CreateOrderDTO, UpdateOrderDTO

    dto = CreateOrderDTO if method == "post" else UpdateOrderDTO
    order = repository.get_by_id.return_value
    return {name: getattr(order, name) for name in dto.model_fields}


def test_client_reads_own_order_but_not_another_or_missing(auth_client, orders_repository):
    client, _ = auth_client
    auth = headers(login(client, cpf="11144477735").json())
    response = client.get("/orders/7", headers=auth)
    assert response.status_code == 200
    assert response.json()["client_id"] == 2
    orders_repository.get_by_id.return_value.client_id = 3
    forbidden = client.get("/orders/7", headers=auth)
    orders_repository.get_by_id.return_value = None
    missing = client.get("/orders/999", headers=auth)
    assert forbidden.status_code == missing.status_code == 404
    assert forbidden.json() == missing.json()


def test_client_list_uses_authenticated_owner_and_pagination(auth_client, orders_repository):
    client, _ = auth_client
    auth = headers(login(client, cpf="11144477735").json())
    orders_repository.list.return_value = [orders_repository.get_by_id.return_value]
    response = client.get("/orders?client_id=3&offset=1&limit=2", headers=auth)
    assert response.status_code == 200
    assert [order["client_id"] for order in response.json()] == [2]
    orders_repository.list.assert_awaited_once_with(client_id=2, offset=1, limit=2)


@pytest.mark.parametrize("method", ["post", "patch", "delete"])
@pytest.mark.parametrize("owner", [2, 3])
def test_client_cannot_write_orders(auth_client, orders_repository, method, owner):
    client, _ = auth_client
    auth = headers(login(client, cpf="11144477735").json())
    orders_repository.get_by_id.return_value.client_id = owner
    kwargs = {} if method == "delete" else {"json": order_payload(orders_repository, method)}
    response = getattr(client, method)("/orders" if method == "post" else "/orders/7", headers=auth, **kwargs)
    assert response.status_code == 403
    for operation in ("get_by_id", "save", "update", "delete"):
        getattr(orders_repository, operation).assert_not_awaited()


@pytest.mark.parametrize("role", [UserRole.ADMIN, UserRole.MANAGER, UserRole.TECHNICAL, UserRole.FINANCIAL])
def test_staff_retains_order_access(auth_client, orders_repository, role):
    client, session = auth_client
    session.get(UserModel, 1).role = role
    session.commit()
    auth = headers(login(client).json())
    orders_repository.list.return_value = [orders_repository.get_by_id.return_value]
    assert client.get("/orders", headers=auth).status_code == 200
    orders_repository.list.assert_awaited_once_with(client_id=None, offset=0, limit=100)
    assert client.get("/orders/7", headers=auth).status_code == 200
    assert client.post("/orders", headers=auth, json=order_payload(orders_repository, "post")).status_code == 201
    assert client.patch("/orders/7", headers=auth, json=order_payload(orders_repository, "patch")).status_code == 200
    assert client.delete("/orders/7", headers=auth).status_code == 204
    orders_repository.save.assert_awaited_once()
    orders_repository.update.assert_awaited_once()
    orders_repository.delete.assert_awaited_once()


@pytest.mark.parametrize("method", ["get", "post", "patch", "delete"])
def test_orders_reject_anonymous_requests(auth_client, orders_repository, method):
    client, _ = auth_client
    kwargs = {"json": order_payload(orders_repository, method)} if method in {"post", "patch"} else {}
    response = getattr(client, method)("/orders" if method == "post" else "/orders/7", **kwargs)
    assert response.status_code == 401
    orders_repository.save.assert_not_awaited()
    orders_repository.update.assert_not_awaited()
    orders_repository.delete.assert_not_awaited()


@pytest.fixture
def auth_client(monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", SecretStr(KEY))
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    UserModel.__table__.create(engine)
    with Session(engine) as session:
        encoded = hash_password(PASSWORD)
        for user_id, cpf, role in [(1, CPF, UserRole.ADMIN), (2, "11144477735", UserRole.CLIENT)]:
            session.add(UserModel(
                id=user_id, primary_name="Fernando", secondary_name="Silva",
                cpf=cpf, email=f"user{user_id}@example.com", role=role,
                cep="01001000", street="Praça da Sé", neighborhood="Sé",
                city="São Paulo", state="SP",
                password_hash=encoded,
            ))
        session.commit()
        async_session = AsyncMock(spec=AsyncSession)
        for method in ("get", "scalar", "scalars", "execute", "commit", "refresh", "delete"):
            getattr(async_session, method).side_effect = getattr(session, method)
        async_session.add.side_effect = session.add
        application = create_app(
            user_repository=SQLAlchemyUserRepository(async_session),
            credential_repository=SQLAlchemyCredentialRepository(async_session),
        )
        with TestClient(application) as client:
            yield client, session
    engine.dispose()


def login(client, cpf=CPF, password=PASSWORD):
    return client.post("/auth/login", json={"cpf": cpf, "password": password})


def headers(pair):
    return {"Authorization": f"Bearer {pair['access_token']}"}


def test_login_me_and_admin_access(auth_client):
    client, session = auth_client
    response = login(client)
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    pair = response.json()
    assert pair["token_type"] == "bearer"
    assert pair["expires_in"] == 900
    claims = TokenManager(settings).decode(pair["access_token"], "access")
    assert claims == (1, 1)
    me = client.get("/auth/me", headers=headers(pair))
    assert me.status_code == 200
    assert me.json()["id"] == 1
    assert "password" not in me.text and "token_version" not in me.text
    assert client.get("/users", headers=headers(pair)).status_code == 200
    stored = session.get(UserModel, 1).password_hash
    assert stored.startswith("$argon2id$") and stored != PASSWORD


@pytest.mark.parametrize("cpf,password", [(CPF, "wrong"), ("12345678909", PASSWORD)])
def test_invalid_credentials(auth_client, cpf, password):
    client, _ = auth_client
    response = login(client, cpf, password)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"detail": "Credenciais ou token inválidos"}


def test_missing_credentials_cannot_login(auth_client):
    client, session = auth_client
    session.get(UserModel, 1).password_hash = None
    session.commit()
    assert login(client).status_code == 401


def test_refresh_rotates_once_and_logout_revokes(auth_client):
    client, _ = auth_client
    pair = login(client).json()
    renewed = client.post("/auth/refresh", json={"refresh_token": pair["refresh_token"]})
    assert renewed.status_code == 200
    new_pair = renewed.json()
    assert new_pair != pair
    assert client.get("/auth/me", headers=headers(pair)).status_code == 401
    assert client.post("/auth/refresh", json={"refresh_token": pair["refresh_token"]}).status_code == 401
    assert client.get("/auth/me", headers=headers(new_pair)).status_code == 200
    assert client.post("/auth/logout", headers=headers(new_pair)).status_code == 204
    assert client.get("/auth/me", headers=headers(new_pair)).status_code == 401
    assert client.post("/auth/refresh", json={"refresh_token": new_pair["refresh_token"]}).status_code == 401


def test_new_login_revokes_previous_session(auth_client):
    client, _ = auth_client
    old = login(client).json()
    new = login(client).json()
    assert client.get("/auth/me", headers=headers(old)).status_code == 401
    assert client.get("/auth/me", headers=headers(new)).status_code == 200


def test_change_password_requires_current_password_and_revokes_tokens(auth_client):
    client, session = auth_client
    pair = login(client).json()
    def change(old, new):
        return client.post("/auth/change-password", headers=headers(pair), json={
            "current_password": old, "new_password": new,
        })
    assert change("wrong", NEW_PASSWORD).status_code == 401
    assert change(PASSWORD, "short").status_code == 422
    assert change(PASSWORD, PASSWORD).status_code == 422
    assert change(PASSWORD, NEW_PASSWORD).status_code == 204
    assert verify_password(NEW_PASSWORD, session.get(UserModel, 1).password_hash)
    assert client.get("/auth/me", headers=headers(pair)).status_code == 401
    assert client.post("/auth/refresh", json={"refresh_token": pair["refresh_token"]}).status_code == 401
    assert login(client).status_code == 401
    assert login(client, password=NEW_PASSWORD).status_code == 200


@pytest.mark.parametrize("path", ["/auth/me", "/users", "/vehicles", "/stock", "/budgets", "/orders"])
def test_business_routes_require_bearer(auth_client, path):
    client, _ = auth_client
    response = client.get(path)
    assert response.status_code == 401, response.text


def test_non_admin_cannot_manage_users_or_escalate_role(auth_client):
    client, _ = auth_client
    pair = login(client, cpf="11144477735").json()
    assert client.get("/auth/me", headers=headers(pair)).status_code == 200
    for method, url, kwargs in [
        ("get", "/users", {}), ("get", "/users/1", {}),
        ("post", "/users", {"json": {}}),
        ("patch", "/users/2", {"json": {"role": "admin"}}),
        ("delete", "/users/1", {}),
    ]:
        assert getattr(client, method)(url, headers=headers(pair), **kwargs).status_code == 403


def test_token_types_cannot_be_interchanged(auth_client):
    client, _ = auth_client
    pair = login(client).json()
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {pair['refresh_token']}"}).status_code == 401
    assert client.post("/auth/refresh", json={"refresh_token": pair["access_token"]}).status_code == 401


@pytest.mark.parametrize("alteration", ["expired", "signature", "issuer", "audience", "missing_exp", "algorithm", "version", "subject"])
def test_invalid_tokens_rejected(auth_client, alteration):
    client, _ = auth_client
    pair = login(client).json()
    claims = jwt.decode(pair["access_token"], KEY, algorithms=["HS256"], audience=settings.JWT_AUDIENCE)
    key, algorithm = KEY, "HS256"
    if alteration == "expired":
        claims["exp"] = datetime.now(timezone.utc) - timedelta(seconds=1)
    elif alteration == "signature":
        key = "another-secret-key-with-at-least-32-characters"
    elif alteration == "issuer":
        claims["iss"] = "other"
    elif alteration == "audience":
        claims["aud"] = "other"
    elif alteration == "missing_exp":
        del claims["exp"]
    elif alteration == "algorithm":
        algorithm = "HS384"
    elif alteration == "version":
        claims["ver"] = True
    elif alteration == "subject":
        claims["sub"] = "0"
    token = jwt.encode(claims, key, algorithm=algorithm)
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_deleted_user_invalidates_token(auth_client):
    client, session = auth_client
    pair = login(client).json()
    session.execute(UserModel.__table__.delete().where(UserModel.id == 1))
    session.commit()
    assert session.get(UserModel, 1) is None
    assert client.get("/auth/me", headers=headers(pair)).status_code == 401


@pytest.mark.asyncio
async def test_stale_credential_cannot_rotate_or_replace_password(auth_client):
    client, session = auth_client
    repository = client.app.state.credential_repository
    credential = await repository.get(1)
    assert await repository.rotate(credential)
    assert not await repository.rotate(credential, hash_password(NEW_PASSWORD))
    session.expire_all()
    assert verify_password(PASSWORD, session.get(UserModel, 1).password_hash)


def test_unconfigured_signing_key_fails_closed(auth_client, monkeypatch):
    client, _ = auth_client
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", None)
    assert login(client).status_code == 503
    assert client.get("/users").status_code == 401


def test_validation_does_not_echo_secrets(auth_client):
    client, _ = auth_client
    secret = "private-password-" * 20
    response = login(client, password=secret)
    assert response.status_code == 422
    assert secret not in response.text
    pair = login(client).json()
    response = client.post("/auth/change-password", headers=headers(pair), json={
        "current_password": PASSWORD, "new_password": "secret",
    })
    assert response.status_code == 422
    assert "secret" not in response.text


@pytest.mark.asyncio
@pytest.mark.parametrize("has_credential", [True, False])
async def test_administrative_password_provisioning(auth_client, monkeypatch, has_credential):
    from app.shared.infrastructure.security import set_password as command

    client, session = auth_client
    old_pair = login(client).json()
    if not has_credential:
        session.get(UserModel, 1).password_hash = None
        session.commit()

    @asynccontextmanager
    async def context():
        yield client.app.state.user_repository.session

    monkeypatch.setattr(command, "AsyncSessionLocal", context)
    monkeypatch.setattr(command, "engine", SimpleNamespace(dispose=AsyncMock()))
    await command.set_password(CPF, NEW_PASSWORD)
    assert verify_password(NEW_PASSWORD, session.get(UserModel, 1).password_hash)
    assert client.get("/auth/me", headers=headers(old_pair)).status_code == 401
    assert login(client, password=NEW_PASSWORD).status_code == 200
    with pytest.raises(ValueError, match="Usuário não encontrado"):
        await command.set_password("12345678909", NEW_PASSWORD)
