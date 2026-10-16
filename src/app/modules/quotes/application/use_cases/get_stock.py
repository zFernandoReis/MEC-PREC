from app.modules.quotes.application.ports.stock_repository import StockRepository
from app.modules.quotes.domain.entities.stock import Stock
from app.modules.quotes.exceptions import StockNotFoundError


class GetStockUseCase:
    def __init__(self, stock_repository: StockRepository):
        self.stock_repository = stock_repository

    async def execute(self, tool_id: str) -> Stock:
        stock = await self.stock_repository.get_by_id(tool_id)
        if stock is None:
            raise StockNotFoundError()
        return stock
