
from app.modules.orders.application.dtos.notification_dto import CreateNotificationDTO
from app.modules.orders.application.ports.notification_repository import NotificationRepository
from app.modules.orders.domain.entities.notification import Notification
from app.modules.orders.domain.enums.order_status import OrderStatus
from app.shared.infrastructure.logging import logger


class CreateNotificationUseCase:

    def __init__(self, notification_repository: NotificationRepository):
        self.notification_repository = notification_repository

    async def execute(self, dto: CreateNotificationDTO) -> Notification:
        logger.debug("Iniciando criação de notificação.")

        if dto.order_status not in OrderStatus:
            logger.debug("Status de ordem de serviço inválido: %s", dto.order_status)
            raise ValueError(f"Status de ordem de serviço inválido: {dto.order_status}")


        notification = Notification(
            notification_type=dto.notification_type,
            client_id=dto.client_id,
            client_email=dto.client_email,
            client_name=dto.client_name,
            order_id=dto.order_id,
            technical_id=dto.technical_id,
            technical_name=dto.technical_name,
            technical_email=dto.technical_email,
            technical_responser_id=dto.technical_responser_id,
            technical_responser_name=dto.technical_responser_name,
            technical_responser_email=dto.technical_responser_email,
            vehicle_id=dto.vehicle_id,
            service_name=dto.service_name,
            service_description=dto.service_description,
            service_date_start=dto.service_date_start,
            service_date_end=dto.service_date_end,
            duration_service_days=dto.duration_service_days,
            order_status=dto.order_status,
        )

        logger.debug("Persistindo nova notificação.")
        await self.notification_repository.save(notification)
        logger.debug("Notificação criada: notification_id=%s", notification.notification_id)

        return notification
