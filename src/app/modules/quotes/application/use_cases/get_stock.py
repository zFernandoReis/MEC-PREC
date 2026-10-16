from app.modules.quotes.application.ports.stock_repository import StockRepository
from app.modules.quotes.domain.entities.stock import Stock
from app.modules.quotes.exceptions import StockNotFoundError
from app.shared.infrastructure.logging import logger


class GetStockUseCase:
    def __init__(self, stock_repository: StockRepository):
        self.stock_repository = stock_repository

    async def execute(self, tool_id: str) -> Stock:
        logger.debug("Consultando item de estoque: tool_id=%s", tool_id)
        stock = await self.stock_repository.get_by_id(tool_id)
        if stock is None:
            logger.debug("Item de estoque não encontrado: tool_id=%s", tool_id)
            raise StockNotFoundError()
        logger.debug("Item de estoque encontrado: tool_id=%s", tool_id)
        return stock
