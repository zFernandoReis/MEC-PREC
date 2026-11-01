from app.modules.quotes.application.ports.stock_repository import StockRepository
from app.modules.quotes.domain.entities.stock import Stock
from app.shared.infrastructure.logging import logger


class ListStocksUseCase:
    def __init__(self, stock_repository: StockRepository):
        self.stock_repository = stock_repository

    async def execute(self, *, offset: int = 0, limit: int = 100) -> list[Stock]:
        logger.debug("Listando estoque: offset=%s, limit=%s", offset, limit)
        stocks = await self.stock_repository.list(offset=offset, limit=limit)
        logger.debug("Listagem de estoque concluída: quantidade=%s", len(stocks))
        return stocks
