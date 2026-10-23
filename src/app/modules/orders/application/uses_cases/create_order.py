from datetime import date, timedelta

from app.modules.orders.application.dtos.order_dto import CreateOrderDTO
from app.modules.orders.domain.entities.orders import Order
from app.modules.orders.domain.enums.order_status import OrderStatus
from app.shared.infrastructure.logging import logger


class CreateOrderUseCase:

    def __init__(
        self,
          order_repository,    ):
        self.order_repository = order_repository

    async def execute(self, dto: CreateOrderDTO):
        logger.debug("Iniciando criação de ordem de serviço com os dados: %s", dto)

        if dto.order_status not in OrderStatus:
            logger.debug("Status de ordem de serviço inválido: %s", dto.order_status)
            raise ValueError(f"Status de ordem de serviço inválido: {dto.order_status}")

        duration_service_days = None
        if dto.duration_service_hours is not None:
            duration_service_days = dto.duration_service_hours / 24

        service_date_start = date.today()


        service_date_end = service_date_start + timedelta(days=duration_service_days) if duration_service_days is not None else None

        order = Order(
            client_id=dto.client_id,
            client_email=dto.client_email,
            technical_id=dto.technical_id,
            technical_name=dto.technical_name,
            technical_email=dto.technical_email,
            budget_id=dto.budget_id,
            technical_responser_id=dto.technical_responser_id,
            technical_responser_name=dto.technical_responser_name,
            technical_responser_email=dto.technical_responser_email,
            vehicle_id=dto.vehicle_id,
            service_name=dto.service_name,
            service_description=dto.service_description,
            service_date_start=service_date_start,
            service_date_end=service_date_end,
            duration_service_hours=dto.duration_service_hours,
            duration_service_days=duration_service_days,
            order_status=dto.order_status,
        )

        logger.debug("Persistindo novo pedido.")
        await self.order_repository.save(order)
        logger.debug("Pedido criado: order_id=%s", order.order_id)

        return order
