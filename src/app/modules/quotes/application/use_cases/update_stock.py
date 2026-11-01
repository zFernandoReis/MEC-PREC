
from app.modules.quotes.application.dtos.stock_dto import UpdateStockDTO
from app.modules.quotes.application.ports.stock_repository import StockRepository
from app.modules.quotes.exceptions import StockNotFoundError
from app.shared.infrastructure.logging import logger


class UpdateStockUseCase:

    def __init__(
        self,
        stock_repository: StockRepository,
    ):
        self.stock_repository = stock_repository

    async def execute(self, tool_id: str, dto: UpdateStockDTO):
        logger.debug("Buscando item de estoque para atualização: tool_id=%s", tool_id)

        stock = await self.stock_repository.get_by_id(tool_id)

        if stock is None:
            logger.debug("Item de estoque não encontrado para atualização: tool_id=%s", tool_id)
            raise StockNotFoundError()


        
        for field in ("tool_name", "quantity", "price", "batch", "replacement_time_hours", "replacement_time_days", "tool_description"):
            value = getattr(dto, field)
            if value is not None:
                setattr(stock, field, value)

        logger.debug("Persistindo alterações do estoque: tool_id=%s", tool_id)
        await self.stock_repository.update(stock)
        logger.debug("Item de estoque atualizado: tool_id=%s", tool_id)

        return stock
