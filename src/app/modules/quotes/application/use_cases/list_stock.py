from app.modules.quotes.application.ports.stock_repository import StockRepository
from app.modules.quotes.domain.entities.stock import Stock


class ListStocksUseCase:
    def __init__(self, stock_repository: StockRepository):
        self.stock_repository = stock_repository

    async def execute(self, *, offset: int = 0, limit: int = 100) -> list[Stock]:
        return await self.stock_repository.list(offset=offset, limit=limit)
