from unittest.mock import AsyncMock
from dataclasses import asdict

import pytest
from fastapi.testclient import TestClient

from app.modules.orders.application.dtos.order_dto import UpdateOrderDTO
from app.modules.orders.application.exceptions import OrderNotFoundError
from app.modules.orders.application.ports.order_repository import OrderRepository
from app.modules.orders.application.use_cases.update_order import UpdateOrderUseCase
from app.modules.orders.domain.entities.orders import Order
from app.modules.orders.domain.enums.order_status import OrderStatus


@pytest.fixture
def order():
    return Order(
        order_id=7, client_id=1, client_email="client@example.com",
        technical_id=2, technical_name="Técnico", technical_email="tech@example.com",
        technical_responser_id=3, technical_responser_name="Responsável",
        technical_responser_email="responsible@example.com", budget_id=4,
        vehicle_id=5, service_name="Revisão", service_description="Descrição original",
        duration_service_hours=24, duration_service_days=1,
        order_status=OrderStatus.RECEBIDA,
    )


@pytest.fixture
def payload():
    return {
        "client_id": 11, "client_email": "newclient@example.com",
        "technical_id": 12, "technical_name": "Novo técnico",
        "technical_email": "newtech@example.com", "technical_responser_id": 13,
        "technical_responser_name": "Novo responsável",
        "technical_responser_email": "newresponsible@example.com",
        "budget_id": 14, "vehicle_id": 15, "service_name": "Troca de óleo",
        "service_description": "Trocar óleo e filtro",
        "duration_service_hours": 48, "duration_service_days": 2,
        "order_status": "em_execucao",
    }


def test_patch_updates_order_fields_and_relationships(authenticated_app, order, payload):
    repository = AsyncMock(spec=OrderRepository)
    repository.get_by_id.return_value = order
    original_system_id = order.system_id

    with TestClient(authenticated_app(order_repository=repository)) as client:
        response = client.patch("/orders/7", json=payload)

    assert response.status_code == 200, response.text
    for field, value in payload.items():
        assert response.json()[field] == value
        assert getattr(order, field) == value
    assert order.order_status is OrderStatus.EM_EXECUCAO
    assert order.order_id == 7
    assert order.system_id == original_system_id
    repository.get_by_id.assert_awaited_once_with(7)
    repository.update.assert_awaited_once_with(order)


@pytest.mark.asyncio
@pytest.mark.parametrize("clear_description", [False, True])
async def test_description_is_preserved_if_omitted_and_cleared_if_null(
    order, payload, clear_description,
):
    payload.pop("service_description")
    if clear_description:
        payload["service_description"] = None
    repository = AsyncMock(spec=OrderRepository)
    repository.get_by_id.return_value = order

    await UpdateOrderUseCase(repository).execute(7, UpdateOrderDTO(**payload))

    assert order.service_description == (None if clear_description else "Descrição original")
    repository.update.assert_awaited_once_with(order)


@pytest.mark.asyncio
async def test_missing_order_does_not_update(payload):
    repository = AsyncMock(spec=OrderRepository)
    repository.get_by_id.return_value = None

    with pytest.raises(OrderNotFoundError):
        await UpdateOrderUseCase(repository).execute(999, UpdateOrderDTO(**payload))

    repository.update.assert_not_awaited()


def test_patch_preserves_omitted_fields(authenticated_app, order):
    repository = AsyncMock(spec=OrderRepository)
    repository.get_by_id.return_value = order
    original = asdict(order)
    with TestClient(authenticated_app(order_repository=repository)) as client:
        response = client.patch("/orders/7", json={"service_name": "Alinhamento"})
    assert response.status_code == 200, response.text
    assert asdict(order) == {**original, "service_name": "Alinhamento"}
    repository.update.assert_awaited_once_with(order)


@pytest.mark.parametrize("field", ["service_description", "duration_service_days"])
def test_patch_can_clear_nullable_fields(authenticated_app, order, field):
    repository = AsyncMock(spec=OrderRepository)
    repository.get_by_id.return_value = order
    with TestClient(authenticated_app(order_repository=repository)) as client:
        response = client.patch("/orders/7", json={field: None})
    assert response.status_code == 200, response.text
    assert response.json()[field] is None
    assert getattr(order, field) is None


@pytest.mark.parametrize("payload", [
    {"client_id": None}, {"order_status": None}, {"service_name": None},
    {"duration_service_hours": None}, {"order_status": "invalid"}, {"order_id": 8},
])
def test_patch_invalid_payload_does_not_persist(authenticated_app, order, payload):
    repository = AsyncMock(spec=OrderRepository)
    repository.get_by_id.return_value = order
    with TestClient(authenticated_app(order_repository=repository)) as client:
        response = client.patch("/orders/7", json=payload)
    assert response.status_code == 422
    repository.update.assert_not_awaited()


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_missing_order_returns_404(authenticated_app, method):
    repository = AsyncMock(spec=OrderRepository)
    repository.get_by_id.return_value = None
    with TestClient(authenticated_app(order_repository=repository)) as client:
        kwargs = {"json": {"service_name": "Alinhamento"}} if method == "patch" else {}
        response = getattr(client, method)("/orders/999", **kwargs)
    assert response.status_code == 404
    assert response.json() == {"detail": "Ordem de serviço não encontrada"}
    repository.update.assert_not_awaited()
    repository.delete.assert_not_awaited()


def test_delete_order_returns_empty_204(authenticated_app, order):
    repository = AsyncMock(spec=OrderRepository)
    repository.get_by_id.return_value = order
    with TestClient(authenticated_app(order_repository=repository)) as client:
        response = client.delete("/orders/7")
    assert response.status_code == 204
    assert response.content == b""
    repository.get_by_id.assert_awaited_once_with(7)
    repository.delete.assert_awaited_once_with(order)
