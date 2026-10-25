from dataclasses import replace
from datetime import date
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.modules.orders.application.dtos.notification_dto import CreateNotificationDTO
from app.modules.orders.application.exceptions import NotificationNotFoundError
from app.modules.orders.application.uses_cases.create_notification import CreateNotificationUseCase
from app.modules.orders.application.uses_cases.delete_notification import DeleteNotificationUseCase
from app.modules.orders.application.uses_cases.get_notification import GetNotificationUseCase
from app.modules.orders.domain.entities.notification import Notification
from app.modules.orders.domain.enums.order_status import OrderStatus
from app.modules.orders.infrastructure.models.notification_model import NotificationModel
from app.modules.orders.infrastructure.repositories.sqlalchemy_notification_repository import (
    SQLAlchemyNotificationRepository,
)


@pytest.fixture
def notification_data():
    return dict(
        client_id=1, client_email="client@example.com", client_name="Cliente",
        technical_id=2, technical_name="Técnico", technical_email="tech@example.com",
        technical_responser_id=3, technical_responser_name="Responsável",
        technical_responser_email="responsible@example.com", vehicle_id=4,
        order_id=5, service_name="Revisão", order_status=OrderStatus.RECEBIDA,
    )


async def test_notification_persistence_and_use_cases(notification_data):
    engine = create_engine("sqlite://")
    NotificationModel.__table__.create(engine)
    try:
        with Session(engine) as sync_session:
            session = AsyncMock(spec=AsyncSession)
            for method in ("add", "commit", "refresh", "get", "scalars", "delete"):
                getattr(session, method).side_effect = getattr(sync_session, method)
            repository = SQLAlchemyNotificationRepository(session)
            notification = await CreateNotificationUseCase(repository).execute(
                CreateNotificationDTO(**notification_data)
            )
            assert isinstance(notification.notification_id, UUID)
            assert notification.create_at is not None
            assert notification.update_at is not None
            assert notification.client_name == notification_data["client_name"]
            assert notification.order_id == notification_data["order_id"]
            assert await GetNotificationUseCase(repository).execute(
                notification.notification_id
            ) == notification

            second = replace(notification, notification_id=None, system_id=uuid4())
            await repository.save(second)
            page = await repository.list(offset=0, limit=1)
            next_page = await repository.list(offset=1, limit=1)
            assert len(page) == len(next_page) == 1
            assert {page[0].notification_id, next_page[0].notification_id} == {
                notification.notification_id, second.notification_id
            }
            assert await repository.list(offset=2, limit=1) == []

            updated = replace(
                notification, client_id=11, client_email="new@example.com", client_name="Novo",
                technical_id=12, technical_name="Outro", technical_email="other@example.com",
                technical_responser_id=13, technical_responser_name="Outro responsável",
                technical_responser_email="newresponsible@example.com", vehicle_id=14,
                order_id=15, service_name="Troca de óleo", service_description="Óleo e filtro",
                duration_service_days=2, order_status=OrderStatus.FINALIZADA,
                service_date_start=date(2026, 10, 25), service_date_end=date(2026, 10, 27),
            )
            await repository.update(updated)
            assert await repository.get_by_id(updated.notification_id) == updated
            assert NotificationModel.from_entity(updated).to_entity() == updated
            updated.order_id = None
            updated.service_description = None
            updated.duration_service_days = None
            updated.service_date_start = None
            updated.service_date_end = None
            await repository.update(updated)
            assert await repository.get_by_id(updated.notification_id) == updated

            await DeleteNotificationUseCase(repository).execute(updated.notification_id)
            assert await repository.get_by_id(updated.notification_id) is None
            for use_case in (GetNotificationUseCase, DeleteNotificationUseCase):
                with pytest.raises(NotificationNotFoundError):
                    await use_case(repository).execute(updated.notification_id)
    finally:
        engine.dispose()


@pytest.mark.parametrize("method", ["update", "delete"])
async def test_missing_notification_does_not_commit(notification_data, method):
    session = AsyncMock(spec=AsyncSession)
    session.get.return_value = None
    notification = Notification(**notification_data, notification_id=uuid4())
    repository = SQLAlchemyNotificationRepository(session)
    with pytest.raises(NotificationNotFoundError):
        await getattr(repository, method)(notification)
    session.get.assert_awaited_once_with(NotificationModel, notification.notification_id)
    session.commit.assert_not_awaited()
    session.delete.assert_not_awaited()
