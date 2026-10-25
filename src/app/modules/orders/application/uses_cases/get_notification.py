from uuid import UUID

from app.modules.orders.application.exceptions import NotificationNotFoundError
from app.modules.orders.application.ports.notification_repository import NotificationRepository
from app.modules.orders.domain.entities.notification import Notification
from app.shared.infrastructure.logging import logger


class GetNotificationUseCase:
    def __init__(self, notification_repository: NotificationRepository):
        self.notification_repository = notification_repository

    async def execute(self, notification_id: UUID) -> Notification:
        logger.debug("Consultando notificação: notification_id=%s", notification_id)
        notification = await self.notification_repository.get_by_id(notification_id)
        if notification is None:
            raise NotificationNotFoundError()
        return notification
