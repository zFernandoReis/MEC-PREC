
from app.modules.orders.application.dtos.order_dto import UpdateOrderDTO
from app.modules.orders.application.exceptions import OrderNotFoundError
from app.modules.orders.application.ports.order_repository import OrderRepository
from app.modules.orders.domain.entities.orders import Order
from app.shared.infrastructure.logging import logger


class UpdateOrderUseCase:

    def __init__(
        self,
        order_repository: OrderRepository,
    ):
        self.order_repository = order_repository

    async def execute(self, order_id: int, dto: UpdateOrderDTO) -> Order:
        logger.debug("Buscando ordem de serviço para atualização: order_id=%s", order_id)

        order = await self.order_repository.get_by_id(order_id)

        if order is None:
            logger.debug("Ordem de serviço não encontrada para atualização: order_id=%s", order_id)
            raise OrderNotFoundError()

        for field, value in dto.model_dump(exclude_unset=True).items():
            setattr(order, field, value)

        logger.debug("Persistindo alterações da ordem de serviço: order_id=%s", order_id)
        await self.order_repository.update(order)
        logger.debug("Ordem de serviço atualizada: order_id=%s", order_id)

        return order

