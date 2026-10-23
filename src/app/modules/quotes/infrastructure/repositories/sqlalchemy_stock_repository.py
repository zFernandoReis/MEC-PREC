from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.quotes.domain.entities.stock import Stock
from app.modules.quotes.exceptions import StockNotFoundError
from app.modules.quotes.infrastructure.models.stock_model import StockModel
from app.shared.infrastructure.logging import logger


class SQLAlchemyStockRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, stock: Stock) -> None:
        logger.debug("Inserindo item de estoque no banco de dados.")
        model = StockModel.from_entity(stock)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        logger.debug("Inserção de item de estoque concluída: tool_id=%s", model.tool_id)
        stock.tool_id = model.tool_id
        stock.create_at = model.create_at
        stock.update_at = model.update_at

    async def get_by_id(self, tool_id: str) -> Stock | None:
        logger.debug("Consultando item de estoque no banco: tool_id=%s", tool_id)
        model = await self.session.get(StockModel, tool_id)
        logger.debug("Consulta de item de estoque concluída: encontrado=%s", model is not None)
        return model.to_entity() if model is not None else None

    async def get_by_ids(self, tool_ids: list[str]) -> list[Stock]:
        if not tool_ids:
            return []
        result = await self.session.scalars(
            select(StockModel).where(StockModel.tool_id.in_(tool_ids))
        )
        return [model.to_entity() for model in result]

    async def list(self, *, offset: int, limit: int) -> list[Stock]:
        logger.debug("Consultando página de item de estoque no banco: offset=%s, limit=%s", offset, limit)
        result = await self.session.scalars(
            select(StockModel).order_by(StockModel.tool_id).offset(offset).limit(limit)
        )
        return [model.to_entity() for model in result]

    async def update(self, stock: Stock) -> None:
        logger.debug("Atualizando item de estoque no banco: tool_id=%s", stock.tool_id)
        model = await self.session.get(StockModel, stock.tool_id)
        if model is None:
            logger.debug("Stock não encontrado no banco: tool_id=%s", stock.tool_id)
            raise StockNotFoundError()
        model.tool_id = stock.tool_id
        model.tool_name = stock.tool_name
        model.price = stock.price
        model.batch = stock.batch
        model.replacement_time_hours = stock.replacement_time_hours
        model.replacement_time_days = stock.replacement_time_days
        model.description = stock.description
        model.quantity = stock.quantity
        await self.session.commit()
        await self.session.refresh(model)
        stock.create_at = model.create_at
        stock.update_at = model.update_at
        logger.debug("Atualização de item de estoque confirmada no banco: tool_id=%s", stock.tool_id)

    async def delete(self, stock: Stock) -> None:
        logger.debug("Excluindo item de estoque no banco: tool_id=%s", stock.tool_id)
        model = await self.session.get(StockModel, stock.tool_id)
        if model is None:
            logger.debug("Stock não encontrado no banco: tool_id=%s", stock.tool_id)
            raise StockNotFoundError()
        await self.session.delete(model)
        await self.session.commit()
        logger.debug("Exclusão de item de estoque confirmada no banco: tool_id=%s", stock.tool_id)
