from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.quotes.domain.entities.stock import Stock
from app.modules.quotes.exceptions import StockNotFoundError
from app.modules.quotes.infrastructure.models.stock_model import StockModel


class SQLAlchemyStockRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, stock: Stock) -> None:
        model = StockModel.from_entity(stock)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        stock.tool_id = model.tool_id
        stock.create_at = model.create_at
        stock.update_at = model.update_at

    async def get_by_id(self, tool_id: str) -> Stock | None:
        model = await self.session.get(StockModel, tool_id)
        return model.to_entity() if model is not None else None

    async def list(self, *, offset: int, limit: int) -> list[Stock]:
        result = await self.session.scalars(
            select(StockModel).order_by(StockModel.tool_id).offset(offset).limit(limit)
        )
        return [model.to_entity() for model in result]

    async def update(self, stock: Stock) -> None:
        model = await self.session.get(StockModel, stock.tool_id)
        if model is None:
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

    async def delete(self, stock: Stock) -> None:
        model = await self.session.get(StockModel, stock.tool_id)
        if model is None:
            raise StockNotFoundError()
        await self.session.delete(model)
        await self.session.commit()
