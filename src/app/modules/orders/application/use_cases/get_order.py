from app.modules.orders.application.exceptions import OrderNotFoundError
from app.modules.orders.application.ports.order_repository import OrderRepository
from app.modules.orders.domain.entities.orders import Order
from app.shared.infrastructure.logging import logger


class GetOrderUseCase:
    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    async def execute(self, order_id: int, *, client_id: int | None = None) -> Order:
        logger.debug("Consultando ordem de serviço: order_id=%s", order_id)
        order = await self.order_repository.get_by_id(order_id)
        if order is None or (client_id is not None and order.client_id != client_id):
            logger.debug("Ordem de serviço não encontrada: order_id=%s", order_id)
            raise OrderNotFoundError()
        logger.debug("Ordem de serviço encontrada: order_id=%s", order_id)
        return order
