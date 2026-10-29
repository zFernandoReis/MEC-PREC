from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.orders.application.exceptions import OrderNotFoundError
from app.modules.orders.domain.entities.orders import Order
from app.modules.orders.infrastructure.models.orders_model import OrderModel
from app.shared.infrastructure.logging import logger


class SQLAlchemyOrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, order: Order) -> None:
        logger.debug("Inserindo ordem de serviço no banco de dados.")
        model = OrderModel.from_entity(order)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        order.order_id = model.order_id
        order.system_id = model.system_id
        order.create_at = model.create_at
        order.update_at = model.update_at
        logger.debug("Inserção de ordem de serviço concluída: order_id=%s", order.order_id)

    async def get_by_id(self, order_id: int) -> Order | None:
        logger.debug("Consultando ordem de serviço no banco: order_id=%s", order_id)
        model = await self.session.get(OrderModel, order_id)
        return model.to_entity() if model is not None else None

    async def list(self, *, offset: int, limit: int, client_id: int | None = None) -> list[Order]:
        logger.debug("Consultando página de ordens: offset=%s, limit=%s", offset, limit)
        statement = select(OrderModel)
        if client_id is not None:
            statement = statement.where(OrderModel.client_id == client_id)
        result = await self.session.scalars(
            statement.order_by(OrderModel.order_id).offset(offset).limit(limit)
        )
        return [model.to_entity() for model in result]

    async def update(self, order: Order) -> None:
        logger.debug("Atualizando ordem de serviço no banco: order_id=%s", order.order_id)
        model = await self.session.get(OrderModel, order.order_id)
        if model is None:
            raise OrderNotFoundError()
        model.client_id = order.client_id
        model.client_email = order.client_email
        model.technical_id = order.technical_id
        model.technical_name = order.technical_name
        model.technical_email = order.technical_email
        model.technical_responser_id = order.technical_responser_id
        model.technical_responser_name = order.technical_responser_name
        model.technical_responser_email = order.technical_responser_email
        model.budget_id = order.budget_id
        model.vehicle_id = order.vehicle_id
        model.service_name = order.service_name
        model.service_description = order.service_description
        model.duration_service_hours = order.duration_service_hours
        model.duration_service_days = order.duration_service_days
        model.order_status = order.order_status
        model.service_date_start = order.service_date_start
        model.service_date_end = order.service_date_end
        await self.session.commit()
        await self.session.refresh(model)
        order.create_at = model.create_at
        order.update_at = model.update_at
        logger.debug("Atualização de ordem de serviço confirmada: order_id=%s", order.order_id)

    async def delete(self, order: Order) -> None:
        logger.debug("Excluindo ordem de serviço no banco: order_id=%s", order.order_id)
        model = await self.session.get(OrderModel, order.order_id)
        if model is None:
            raise OrderNotFoundError()
        await self.session.delete(model)
        await self.session.commit()
        logger.debug("Exclusão de ordem de serviço confirmada: order_id=%s", order.order_id)
