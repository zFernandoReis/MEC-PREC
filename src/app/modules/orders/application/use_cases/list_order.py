from app.modules.orders.application.ports.order_repository import OrderRepository
from app.modules.orders.domain.entities.orders import Order
from app.shared.infrastructure.logging import logger


class ListOrdersUseCase:
    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    async def execute(self, *, offset: int = 0, limit: int = 100, client_id: int | None = None) -> list[Order]:
        logger.debug("Listando ordens de serviço: offset=%s, limit=%s", offset, limit)
        orders = await self.order_repository.list(offset=offset, limit=limit, client_id=client_id)
        logger.debug("Listagem de ordens de serviço concluída: quantidade=%s", len(orders))
        return orders
