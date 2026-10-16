from app.modules.users.application.exceptions import UserNotFoundError
from app.shared.infrastructure.logging import logger


class DeleteStockUseCase:

    def __init__(self, stock_repository):
        self.stock_repository = stock_repository

    async def execute(self, stock_id: int) -> None:
        logger.debug("Buscando item de estoque para exclusão: tool_id=%s", stock_id)
        stock = await self.stock_repository.get_by_id(stock_id)

        if stock is None:
            logger.debug("Item de estoque não encontrado para exclusão: tool_id=%s", stock_id)
            raise UserNotFoundError()

        await self.stock_repository.delete(stock)
        logger.debug("Item de estoque excluído: tool_id=%s", stock_id)
