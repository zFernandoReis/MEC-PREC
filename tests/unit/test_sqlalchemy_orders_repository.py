from dataclasses import replace
from datetime import date
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.modules.orders.application.exceptions import OrderNotFoundError
from app.modules.orders.domain.entities.orders import Order
from app.modules.orders.domain.enums.order_status import OrderStatus
from app.modules.orders.infrastructure.models.orders_model import OrderModel
from app.modules.orders.infrastructure.repositories.sqlalchemy_orders_repository import (
    SQLAlchemyOrderRepository,
)


@pytest.fixture
def order():
    return Order(
        client_id=1, client_email="client@example.com",
        technical_id=2, technical_name="Técnico", technical_email="tech@example.com",
        technical_responser_id=3, technical_responser_name="Responsável",
        technical_responser_email="responsible@example.com", budget_id=4,
        vehicle_id=5, service_name="Revisão", duration_service_hours=2.5,
        order_status=OrderStatus.RECEBIDA,
    )


@pytest.mark.asyncio
async def test_order_repository_crud(order):
    engine = create_engine("sqlite://")
    # Isola o CRUD de orders; as chaves estrangeiras são verificadas no teste do modelo.
    OrderModel.__table__.create(engine)
    try:
        with Session(engine) as sync_session:
            session = AsyncMock(spec=AsyncSession)
            for method in ("add", "commit", "refresh", "get", "scalars", "delete"):
                getattr(session, method).side_effect = getattr(sync_session, method)
            repository = SQLAlchemyOrderRepository(session)

            await repository.save(order)
            assert order.order_id == 1
            assert order.create_at is not None
            assert order.update_at is not None
            assert await repository.get_by_id(order.order_id) == order
            assert await repository.get_by_id(999) is None

            second = replace(order, order_id=None, system_id=uuid4())
            await repository.save(second)
            assert await repository.list(offset=0, limit=1) == [order]
            assert await repository.list(offset=1, limit=1) == [second]
            assert await repository.list(offset=2, limit=1) == []

            second.client_id = 2
            await repository.update(second)
            third = replace(order, order_id=None, client_id=2, system_id=uuid4())
            await repository.save(third)
            assert await repository.list(client_id=1, offset=0, limit=10) == [order]
            assert await repository.list(client_id=2, offset=0, limit=1) == [second]
            assert await repository.list(client_id=2, offset=1, limit=1) == [third]
            assert await repository.list(client_id=2, offset=2, limit=1) == []
            assert await repository.list(client_id=999, offset=0, limit=10) == []
            await repository.delete(third)

            sync_session.execute(text(
                "UPDATE orders SET update_at = '2000-01-01 00:00:00' WHERE order_id = 1"
            ))
            sync_session.commit()
            sync_session.expire_all()
            updated = replace(
                order, client_id=11, client_email="newclient@example.com",
                technical_id=12, technical_name="Novo técnico",
                technical_email="newtech@example.com", technical_responser_id=13,
                technical_responser_name="Novo responsável",
                technical_responser_email="newresponsible@example.com",
                budget_id=14, vehicle_id=15, service_name="Troca de óleo",
                service_description="Trocar óleo e filtro", duration_service_hours=3,
                duration_service_days=1, order_status=OrderStatus.FINALIZADA,
                service_date_start=date(2026, 10, 21), service_date_end=date(2026, 10, 22),
            )
            await repository.update(updated)
            assert updated.update_at.year > 2000
            assert await repository.get_by_id(order.order_id) == updated

            updated.service_description = None
            updated.duration_service_days = None
            updated.service_date_start = None
            updated.service_date_end = None
            await repository.update(updated)
            assert await repository.get_by_id(order.order_id) == updated

            await repository.delete(updated)
            assert await repository.get_by_id(order.order_id) is None
            assert await repository.list(offset=0, limit=10) == [second]
    finally:
        engine.dispose()


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["update", "delete"])
async def test_missing_order_raises_without_committing(order, method):
    session = AsyncMock(spec=AsyncSession)
    session.get.return_value = None
    repository = SQLAlchemyOrderRepository(session)
    order.order_id = 999

    with pytest.raises(OrderNotFoundError):
        await getattr(repository, method)(order)

    session.get.assert_awaited_once_with(OrderModel, 999)
    session.commit.assert_not_awaited()
    session.delete.assert_not_awaited()
