from app.modules.orders.application.exceptions import OrderNotFoundError
from app.shared.infrastructure.logging import logger


class DeleteOrderUseCase:

    def __init__(self, order_repository):
        self.order_repository = order_repository

    async def execute(self, order_id: int) -> None:
        logger.debug("Buscando ordem de serviço para exclusão: order_id=%s", order_id)
        order = await self.order_repository.get_by_id(order_id)

        if order is None:
            logger.debug("Ordem de serviço não encontrada para exclusão: order_id=%s", order_id)
            raise OrderNotFoundError()

        await self.order_repository.delete(order)
        logger.debug("Ordem de serviço excluída: order_id=%s", order.order_id)
