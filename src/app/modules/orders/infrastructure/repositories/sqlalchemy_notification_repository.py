from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.orders.application.exceptions import NotificationNotFoundError
from app.modules.orders.domain.entities.notification import Notification
from app.modules.orders.infrastructure.models.notification_model import (
    NotificationModel,
)
from app.shared.infrastructure.logging import logger


class SQLAlchemyNotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, notification: Notification) -> None:
        model = NotificationModel.from_entity(notification)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        notification.notification_id = model.notification_id
        notification.system_id = model.system_id
        notification.create_at = model.create_at
        notification.update_at = model.update_at
        logger.debug("Notificação criada: notification_id=%s", notification.notification_id)

    async def get_by_id(self, notification_id: UUID) -> Notification | None:
        model = await self.session.get(NotificationModel, notification_id)
        return model.to_entity() if model is not None else None

    async def list(self, *, offset: int, limit: int) -> list[Notification]:
        result = await self.session.scalars(
            select(NotificationModel)
            .order_by(NotificationModel.create_at, NotificationModel.notification_id)
            .offset(offset)
            .limit(limit)
        )
        return [model.to_entity() for model in result]

    async def update(self, notification: Notification) -> None:
        model = await self.session.get(NotificationModel, notification.notification_id)
        if model is None:
            raise NotificationNotFoundError()
        model.order_id = notification.order_id
        model.notification_type = notification.notification_type
        model.client_id = notification.client_id
        model.client_email = notification.client_email
        model.client_name = notification.client_name
        model.technical_id = notification.technical_id
        model.technical_name = notification.technical_name
        model.technical_email = notification.technical_email
        model.technical_responser_id = notification.technical_responser_id
        model.technical_responser_name = notification.technical_responser_name
        model.technical_responser_email = notification.technical_responser_email
        model.vehicle_id = notification.vehicle_id
        model.service_name = notification.service_name
        model.service_description = notification.service_description
        model.duration_service_days = notification.duration_service_days
        model.order_status = notification.order_status
        model.service_date_start = notification.service_date_start
        model.service_date_end = notification.service_date_end
        await self.session.commit()
        await self.session.refresh(model)
        notification.create_at = model.create_at
        notification.update_at = model.update_at
        logger.debug("Notificação atualizada: notification_id=%s", notification.notification_id)

    async def delete(self, notification: Notification) -> None:
        model = await self.session.get(NotificationModel, notification.notification_id)
        if model is None:
            raise NotificationNotFoundError()
        await self.session.delete(model)
        await self.session.commit()
        logger.debug("Notificação excluída: notification_id=%s", notification.notification_id)
