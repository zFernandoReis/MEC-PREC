
from app.modules.quotes.application.dtos.stock_dto import UpdateStockDTO
from app.modules.quotes.application.ports.stock_repository import StockRepository
from app.modules.quotes.exceptions import StockNotFoundError


class UpdateStockUseCase:

    def __init__(
        self,
        stock_repository: StockRepository,
    ):
        self.stock_repository = stock_repository

    async def execute(self, tool_id: str, dto: UpdateStockDTO):

        stock = await self.stock_repository.get_by_id(tool_id)

        print(f"Updating stock with tool_id: {tool_id}, dto: {dto}, found stock: {stock}")

        if stock is None:
            raise StockNotFoundError()


        
        for field in ("tool_name", "quantity", "price", "batch", "replacement_time_hours", "replacement_time_days", "tool_description"):
            value = getattr(dto, field)
            if value is not None:
                setattr(stock, field, value)

        await self.stock_repository.update(stock)

        return stock