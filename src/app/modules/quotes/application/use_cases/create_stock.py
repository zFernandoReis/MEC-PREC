import hashlib

from app.modules.quotes.application.dtos.stock_dto import CreateStockDTO
from app.modules.quotes.domain.entities.stock import Stock
from app.shared.infrastructure.logging import logger


class CreateStockUseCase:

    def __init__(
        self,
          stock_repository,    ):
        self.stock_repository = stock_repository

    def generate_id(self, batch: str, name: str) -> str:
        logger.debug("Gerando identificador de estoque a partir do lote e nome normalizados.")
        part_name = name.strip().upper()
        lot_number = batch.strip().upper()

        content = f"{len(part_name)}:{part_name}{len(lot_number)}:{lot_number}"

        hash_value = hashlib.sha256(content.encode("utf-8")).hexdigest()

        prefix = hash_value[:6].upper()
        suffix = int(hash_value[6:14], 16) % 10000

        return f"{prefix}-{suffix:04d}" 

    async def execute(self, dto: CreateStockDTO):
        logger.debug("Iniciando criação de item de estoque.")

        tool_id = self.generate_id(batch=dto.batch, name=dto.tool_name)
        stock = Stock(
            tool_name=dto.tool_name,
            quantity=dto.quantity,
            price=dto.price,
            batch=dto.batch,
            description=dto.tool_description,
            replacement_time_hours=dto.replacement_time_hours,
            replacement_time_days=dto.replacement_time_days,
            tool_id=tool_id
        )

        logger.debug("Persistindo novo item de estoque: tool_id=%s", tool_id)

        await self.stock_repository.save(stock)
        logger.debug("Item de estoque criado: tool_id=%s", stock.tool_id)

        return stock
