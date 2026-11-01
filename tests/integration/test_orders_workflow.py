"""HTTP + JWT + use cases + real repositories in a disposable PostgreSQL schema.

Uses the configured database only to create/drop a uniquely named test schema.
No application table is truncated or modified. PostgreSQL is required.
"""
import asyncio
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import event, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.main import create_app
from app.bootstrap.migrate_order_workflow import migrate_connection
from app.modules.orders.infrastructure.http.dependencies import get_order_repository
from app.modules.orders.infrastructure.models.order_event_model import OrderEventModel
from app.modules.orders.infrastructure.models.orders_model import OrderModel
from app.modules.orders.domain.entities.order_workflow import OrderConflictError
from app.modules.orders.infrastructure.repositories.sqlalchemy_orders_repository import SQLAlchemyOrderRepository
from app.modules.quotes.infrastructure.http.dependencies import get_budget_repository, get_stock_repository
from app.modules.quotes.infrastructure.models.budgets_model import BudgetModel
from app.modules.quotes.infrastructure.repositories.sqlalchemy_budget_repository import SQLAlchemyBudgetRepository
from app.modules.quotes.infrastructure.repositories.sqlalchemy_stock_repository import SQLAlchemyStockRepository
from app.modules.users.infrastructure.http.dependencies import get_user_repository
from app.modules.users.infrastructure.models.users_model import UserModel
from app.modules.users.infrastructure.models.vehicles_model import VehicleModel
from app.modules.users.infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.shared.infrastructure.database.base import Base
from app.shared.infrastructure.database.engine import DATABASE_URL
from app.shared.infrastructure.security.dependencies import get_credential_repository
from app.shared.infrastructure.security.passwords import hash_password
from app.shared.infrastructure.security.repository import SQLAlchemyCredentialRepository

PASSWORD = "integration-orders-password-123"
PEOPLE = [
    (1, "52998224725", "admin"), (2, "11144477735", "client"),
    (3, "12345678909", "technical"), (4, "93541134780", "financial"),
    (5, "39053344705", "manager"), (6, "98765432100", "client"),
    (7, "01234567890", "technical"),
]
ACTIONS = ["start-diagnosis", "request-approval", "approve", "start-execution", "finish", "deliver"]
ENDPOINTS = [("POST", action) for action in ACTIONS] + [("GET", "allowed-actions"), ("GET", "history")]
EXTRA = {
    "request-approval": {"diagnosis": "Filtro e óleo precisam de substituição"},
    "approve": {"evidence": "Consentimento do cliente registrado no atendimento 123"},
    "finish": {"service_report": "Óleo e filtro substituídos; verificação concluída"},
    "deliver": {"received_by": "Cliente de teste"},
}


@pytest.fixture(scope="module")
def password_hash():
    return hash_password(PASSWORD)


@pytest.fixture
async def api(monkeypatch, password_hash):
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", SecretStr("orders-integration-secret-at-least-32-characters"))
    monkeypatch.setattr(settings, "LOG_LEVEL", "WARNING")
    schema = "test_orders_" + uuid4().hex
    admin_engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    test_engine = create_async_engine(
        DATABASE_URL, poolclass=NullPool, connect_args={"server_settings": {"search_path": schema}},
    )
    sessions = async_sessionmaker(test_engine, expire_on_commit=False)
    try:
        async with admin_engine.begin() as connection:
            await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        async with test_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with sessions() as session:
            for user_id, cpf, role in PEOPLE:
                session.add(UserModel(
                    id=user_id, cpf=cpf, role=role, primary_name="Pessoa", secondary_name="Teste",
                    email=f"user{user_id}@example.com", password_hash=password_hash,
                    cep="01001000", street="Praça da Sé", neighborhood="Sé", city="São Paulo", state="SP",
                ))
            await session.flush()
            session.add(VehicleModel(vehicle_id=1, owner_id=2, vehicle_type="car", brand="Marca",
                                     model="Modelo", year_manufacture=2024, year_model=2024,
                                     license_plate="ABC1D23", color="Azul", mileage=100, fuel_type="flex"))
            await session.flush()
            session.add(BudgetModel(budget_id=1, vehicle_id=1, client_id=2, technical_id=3,
                                    technical_name="Técnico", technical_disponibility=True,
                                    service_name="Revisão", amount=100, duration_service_hours=24,
                                    duration_service_days=1, tools=[]))
            await session.commit()
        app = create_app()

        def provider(repository_type):
            async def dependency():
                async with sessions() as session:
                    try:
                        yield repository_type(session)
                    except Exception:
                        await session.rollback()
                        raise
            return dependency

        for dependency, repository_type in (
            (get_order_repository, SQLAlchemyOrderRepository),
            (get_budget_repository, SQLAlchemyBudgetRepository),
            (get_stock_repository, SQLAlchemyStockRepository),
            (get_user_repository, SQLAlchemyUserRepository),
            (get_credential_repository, SQLAlchemyCredentialRepository),
        ):
            app.dependency_overrides[dependency] = provider(repository_type)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            headers = {}
            for user_id, cpf, _ in PEOPLE:
                result = await client.post("/auth/login", json={"cpf": cpf, "password": PASSWORD})
                assert result.status_code == 200, result.text
                headers[user_id] = {"Authorization": "Bearer " + result.json()["access_token"]}
            payload = {
                "client_id": 2, "client_email": "user2@example.com", "technical_id": 3,
                "technical_name": "Técnico", "technical_email": "user3@example.com", "budget_id": 1,
                "vehicle_id": 1, "service_name": "Revisão", "technical_responser_id": 3,
                "technical_responser_name": "Técnico", "technical_responser_email": "user3@example.com",
                "duration_service_hours": 24,
            }
            result = await client.post("/orders", json=payload, headers=headers[1])
            assert result.status_code == 201, result.text
            yield SimpleNamespace(client=client, headers=headers, sessions=sessions, engine=test_engine,
                                  order_id=result.json()["order_id"], payload=payload)
    finally:
        await test_engine.dispose()
        async with admin_engine.begin() as connection:
            # Identifier generated exclusively above; never a user/configured schema.
            await connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await admin_engine.dispose()


async def act(api, action, version, user=1, **extra):
    return await api.client.post(f"/orders/{api.order_id}/{action}", headers=api.headers[user],
                                 json={"expected_version": version, **EXTRA.get(action, {}), **extra})


async def advance(api, count):
    for version, action in enumerate(ACTIONS[:count], 1):
        response = await act(api, action, version)
        assert response.status_code == 200, response.text


async def current(api):
    result = await api.client.get(f"/orders/{api.order_id}", headers=api.headers[1])
    assert result.status_code == 200
    return result.json()


async def test_complete_flow_and_history_with_real_authentication(api):
    initial = await current(api)
    assert initial["order_status"] == "recebida" and initial["version"] == 1
    statuses = ["em_diagnostico", "aguardando_aprovacao", "aguardando_aprovacao", "em_execucao", "finalizada", "entregue"]
    for version, (action, target) in enumerate(zip(ACTIONS, statuses), 1):
        result = await api.client.get(f"/orders/{api.order_id}/allowed-actions", headers=api.headers[1])
        assert result.status_code == 200
        assert result.json()["allowed_actions"] == [action.replace("-", "_")]
        # The responsible technician operates; the client consents; the manager delivers.
        user = 2 if action == "approve" else 5 if action == "deliver" else 3
        response = await act(api, action, version, user=user)
        assert response.status_code == 200, response.text
        assert response.json()["order_status"] == target
        assert response.json()["version"] == version + 1
    final = await current(api)
    assert final["service_date_end"] == initial["service_date_end"]
    assert all(final[field] for field in ("approved_at", "execution_started_at", "finished_at", "delivered_at"))
    assert final["approved_by"] == 2
    assert final["budget_snapshot"]["amount"] == 100
    response = await api.client.get(f"/orders/{api.order_id}/allowed-actions", headers=api.headers[1])
    assert response.json()["allowed_actions"] == []
    history = await api.client.get(f"/orders/{api.order_id}/history", headers=api.headers[1])
    assert history.status_code == 200
    assert [item["action"] for item in history.json()] == [a.replace("-", "_") for a in ACTIONS]
    assert [item["version"] for item in history.json()] == list(range(2, 8))
    assert history.json()[2]["previous_status"] == history.json()[2]["next_status"]
    page = await api.client.get(f"/orders/{api.order_id}/history?offset=1&limit=2", headers=api.headers[1])
    assert page.json() == history.json()[1:3]
    public = await api.client.get(f"/orders/{api.order_id}/history", headers=api.headers[2])
    assert public.status_code == 200 and len(public.json()) == 6
    assert all("details" not in item and "actor_id" not in item for item in public.json())


@pytest.mark.parametrize("method,endpoint", ENDPOINTS)
async def test_every_endpoint_rejects_anonymous_missing_and_foreign_order(api, method, endpoint):
    kwargs = {"json": {"expected_version": 1, **EXTRA.get(endpoint, {})}} if method == "POST" else {}
    path = f"/orders/{api.order_id}/{endpoint}"
    assert (await api.client.request(method, path, **kwargs)).status_code == 401
    assert (await api.client.request(method, f"/orders/999/{endpoint}", headers=api.headers[1], **kwargs)).status_code == 404
    assert (await api.client.request(method, path, headers=api.headers[6], **kwargs)).status_code == 404


@pytest.mark.parametrize("action", ACTIONS)
async def test_every_command_rejects_stale_versions_invalid_input_and_financial_role(api, action):
    index = ACTIONS.index(action)
    await advance(api, index)
    before = await current(api)
    assert (await act(api, action, index + 1, user=4)).status_code == 403
    assert (await act(api, action, 999)).status_code == 409
    assert (await act(api, action, 0)).status_code == 422
    assert (await act(api, action, index + 1, order_status="entregue")).status_code == 422
    assert await current(api) == before


async def test_illegal_jumps_repetitions_and_missing_approval(api):
    for action in ACTIONS[1:]:
        assert (await act(api, action, 1)).status_code == 409
    await advance(api, 2)
    assert (await act(api, "start-execution", 3)).json()["detail"]["code"] == "approval_required"
    assert (await act(api, "approve", 3, evidence=None)).json()["detail"]["code"] == "approval_evidence_required"
    assert (await act(api, "approve", 3)).status_code == 200
    assert (await act(api, "approve", 4)).status_code == 409
    for action in ACTIONS[3:]:
        version = (await current(api))["version"]
        assert (await act(api, action, version)).status_code == 200
    for action in ACTIONS:
        assert (await act(api, action, 7)).status_code == 409


async def test_permissions_owner_responsible_technician_and_reads(api):
    assert (await act(api, "start-diagnosis", 1, user=7)).status_code == 403
    assert (await act(api, "start-diagnosis", 1, user=2)).status_code == 403
    for user in (2, 4, 7):
        result = await api.client.get(f"/orders/{api.order_id}/allowed-actions", headers=api.headers[user])
        assert result.status_code == 200 and result.json()["allowed_actions"] == []
    await advance(api, 2)
    assert (await act(api, "approve", 3, user=3)).status_code == 403
    await act(api, "approve", 3, user=2)
    await act(api, "start-execution", 4, user=3)
    await act(api, "finish", 5, user=3)
    assert (await act(api, "deliver", 6, user=3)).status_code == 403
    assert (await act(api, "deliver", 6, user=5)).status_code == 200


async def test_crud_cannot_bypass_workflow_and_budget_is_frozen(api):
    assert (await api.client.post("/orders", headers=api.headers[1], json={**api.payload, "order_status": "entregue"})).status_code == 422
    path = f"/orders/{api.order_id}"
    assert (await api.client.patch(path, headers=api.headers[1], json={"order_status": "entregue"})).status_code == 422
    assert (await api.client.delete(path, headers=api.headers[1])).status_code == 409
    patch = await api.client.patch(path, headers=api.headers[1], json={"service_description": "Inspecionar"})
    assert patch.status_code == 200 and patch.json()["version"] == 2
    assert (await act(api, "start-diagnosis", 1)).status_code == 409
    assert (await act(api, "start-diagnosis", 2)).status_code == 200
    assert (await act(api, "request-approval", 3)).status_code == 200
    assert (await api.client.patch(path, headers=api.headers[1], json={"client_id": 6})).status_code == 409
    budget = {"technical_name": "Técnico", "technical_disponibility": True, "service_name": "Alterado",
              "amount": 200, "duration_service_hours": 24, "duration_service_days": 1}
    for method, kwargs in (("PATCH", {"json": budget}), ("DELETE", {})):
        result = await api.client.request(method, "/budgets/1", headers=api.headers[1], **kwargs)
        assert result.status_code == 409, result.text
    async with api.sessions() as session:
        assert (await session.get(BudgetModel, 1)).amount == 100


async def test_two_simultaneous_commands_only_commit_once(api):
    results = await asyncio.gather(act(api, "start-diagnosis", 1), act(api, "start-diagnosis", 1))
    assert sorted(r.status_code for r in results) == [200, 409]
    assert (await current(api))["version"] == 2
    response = await api.client.get(f"/orders/{api.order_id}/history", headers=api.headers[1])
    assert len(response.json()) == 1


async def test_history_failure_rolls_back_order_and_budget_lock(api):
    await advance(api, 1)

    def reject_insert(mapper, connection, target):
        raise RuntimeError("simulated audit write failure")

    event.listen(OrderEventModel, "before_insert", reject_insert)
    try:
        with pytest.raises(RuntimeError, match="simulated audit"):
            await act(api, "request-approval", 2)
    finally:
        event.remove(OrderEventModel, "before_insert", reject_insert)
    order = await current(api)
    assert order["version"] == 2 and order["budget_snapshot"] is None
    async with api.sessions() as session:
        assert (await session.get(BudgetModel, 1)).workflow_locked is False
        assert len((await session.scalars(select(OrderEventModel))).all()) == 1


async def test_relationships_and_required_action_details(api):
    path = f"/orders/{api.order_id}"
    await api.client.patch(path, headers=api.headers[1], json={"client_id": 6})
    result = await act(api, "start-diagnosis", 2)
    assert result.status_code == 409 and result.json()["detail"]["code"] == "invalid_order_relationships"
    for action, field in (("request-approval", "diagnosis"), ("finish", "service_report"), ("deliver", "received_by")):
        assert (await act(api, action, 2, **{field: "   "})).status_code == 422
    for query in ("offset=-1", "limit=0", "limit=101"):
        assert (await api.client.get(path + "/history?" + query, headers=api.headers[1])).status_code == 422


async def test_migration_is_repeatable_and_preserves_existing_orders(api):
    before = await current(api)
    async with api.engine.begin() as connection:
        await migrate_connection(connection)
        await migrate_connection(connection)
    assert await current(api) == before


async def test_migration_upgrades_legacy_pending_order_without_inventing_approval(api):
    async with api.engine.begin() as connection:
        await connection.execute(text("UPDATE orders SET order_status = 'aguardando_aprovacao'"))
        await connection.execute(text("DROP TABLE order_events"))
        for column in ("version", "budget_snapshot", "approved_at", "approved_by",
                       "execution_started_at", "finished_at", "delivered_at"):
            await connection.execute(text(f"ALTER TABLE orders DROP COLUMN {column}"))
        await connection.execute(text("ALTER TABLE budgets DROP COLUMN workflow_locked"))
        await migrate_connection(connection)
        await migrate_connection(connection)
    order = await current(api)
    assert order["order_status"] == "aguardando_aprovacao"
    assert order["approved_at"] is None and order["version"] == 1
    assert order["budget_snapshot"]["amount"] == 100
    history = await api.client.get(f"/orders/{api.order_id}/history", headers=api.headers[1])
    assert history.json() == []
    assert (await act(api, "start-execution", 1)).status_code == 409
    assert (await act(api, "approve", 1, user=2)).status_code == 200


async def test_stale_generic_patch_cannot_overwrite_a_transition(api):
    await advance(api, 1)
    async with api.sessions() as session:
        repository = SQLAlchemyOrderRepository(session)
        stale = await repository.get_by_id(api.order_id)
        assert (await act(api, "request-approval", 2)).status_code == 200
        stale.service_name = "Tentativa desatualizada"
        with pytest.raises(OrderConflictError):
            await repository.update(stale)
        await session.rollback()
    order = await current(api)
    assert order["version"] == 3 and order["service_name"] == "Revisão"


async def test_request_approval_waits_for_budget_update_and_freezes_committed_terms(api):
    await advance(api, 1)
    async with api.sessions() as session:
        budget = await session.scalar(select(BudgetModel).where(BudgetModel.budget_id == 1).with_for_update())
        budget.amount = 150
        await session.flush()
        pending = asyncio.create_task(act(api, "request-approval", 2))
        try:
            # Release the budget lock with the new terms committed. The request
            # must see 150 whether it reached the lock before or after release.
            await session.commit()
            result = await asyncio.wait_for(pending, timeout=10)
        finally:
            if not pending.done():
                pending.cancel()
                await asyncio.gather(pending, return_exceptions=True)
        assert result.status_code == 200, result.text
        assert result.json()["budget_snapshot"]["amount"] == 150


async def test_finalization_excludes_order_from_deadline_jobs(api):
    from datetime import date, timedelta
    from app.modules.orders.infrastructure.jobs.notify_upcoming_orders import NotifyUpcomingOrdersJob
    from app.modules.orders.infrastructure.jobs.notify_overdue_orders import NotifyOverdueOrdersJob
    # The isolated fixture may have been initialized before these models were imported.
    from app.modules.orders.infrastructure.models.notification_model import NotificationModel
    async with api.engine.begin() as connection:
        await connection.run_sync(lambda sync: NotificationModel.__table__.create(sync, checkfirst=True))
    await advance(api, 4)
    async with api.sessions() as session:
        order = await session.get(OrderModel, api.order_id)
        order.service_date_end = date.today() - timedelta(days=1)
        await session.commit()
        query = select(OrderModel).where(*NotifyOverdueOrdersJob(session)._deadline_conditions(date.today(), date.today()))
        assert len((await session.scalars(query)).all()) == 1
    assert (await act(api, "finish", 5)).status_code == 200
    async with api.sessions() as session:
        assert (await session.scalars(query)).all() == []
        order = await session.get(OrderModel, api.order_id)
        order.service_date_end = date.today()
        await session.commit()
        upcoming = select(OrderModel).where(*NotifyUpcomingOrdersJob(session)._deadline_conditions(date.today(), date.today()))
        assert (await session.scalars(upcoming)).all() == []
