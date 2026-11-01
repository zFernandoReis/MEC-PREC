from app.modules.orders.application.exceptions import OrderNotFoundError
from app.modules.orders.application.ports.order_repository import OrderRepository
from app.shared.infrastructure.logging import logger
from app.modules.orders.domain.entities.order_workflow import OrderConflictError


class DeleteOrderUseCase:

    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    async def execute(self, order_id: int) -> None:
        logger.debug("Buscando ordem de serviço para exclusão: order_id=%s", order_id)
        order = await self.order_repository.get_by_id(order_id)

        if order is None:
            logger.debug("Ordem de serviço não encontrada para exclusão: order_id=%s", order_id)
            raise OrderNotFoundError()

        raise OrderConflictError("Ordens de serviço devem ser preservadas para auditoria", "order_deletion_disabled")
