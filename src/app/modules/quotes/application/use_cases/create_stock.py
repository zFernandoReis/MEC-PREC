import hashlib

from app.modules.quotes.application.dtos.stock_dto import CreateStockDTO
from app.modules.quotes.domain.entities.stock import Stock


class CreateStockUseCase:

    def __init__(
        self,
          stock_repository,    ):
        self.stock_repository = stock_repository

    def generate_id(self, batch: str, name: str) -> str:
        # Normalização
        part_name = name.strip().upper()
        lot_number = batch.strip().upper()

        # Combinação das duas variáveis
        content = f"{len(part_name)}:{part_name}{len(lot_number)}:{lot_number}"

        # Hash determinístico
        hash_value = hashlib.sha256(content.encode("utf-8")).hexdigest()

        # Formatação: 6 caracteres + 4 números
        prefix = hash_value[:6].upper()
        suffix = int(hash_value[6:14], 16) % 10000

        return f"{prefix}-{suffix:04d}" 

    async def execute(self, dto: CreateStockDTO):

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

        print(f"Creating stock: {stock}")

        await self.stock_repository.save(stock)

        return stock
