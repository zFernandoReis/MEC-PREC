from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.orders.application.exceptions import OrderNotFoundError
from app.modules.orders.domain.entities.orders import Order
from app.modules.orders.infrastructure.models.orders_model import OrderModel
from app.modules.orders.infrastructure.models.order_event_model import OrderEventModel
from app.modules.orders.domain.entities.order_event import OrderEvent
from app.modules.orders.domain.entities.order_workflow import OrderConflictError, OrderContext
from app.modules.orders.domain.enums.order_status import OrderStatus
from app.modules.quotes.infrastructure.models.budgets_model import BudgetModel
from app.modules.users.infrastructure.models.users_model import UserModel
from app.modules.users.infrastructure.models.vehicles_model import VehicleModel
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
        if await self.session.get(OrderModel, order.order_id) is None:
            raise OrderNotFoundError()
        fields = (
            "client_id", "client_email", "technical_id", "technical_name", "technical_email",
            "technical_responser_id", "technical_responser_name", "technical_responser_email",
            "budget_id", "vehicle_id", "service_name", "service_description",
            "duration_service_hours", "duration_service_days", "service_date_start", "service_date_end",
        )
        values = {name: getattr(order, name) for name in fields}
        values["version"] = order.version + 1
        result = await self.session.execute(update(OrderModel).where(
            OrderModel.order_id == order.order_id, OrderModel.version == order.version,
            OrderModel.order_status.in_([OrderStatus.RECEBIDA, OrderStatus.EM_DIAGNOSTICO]),
        ).values(**values))
        if result.rowcount != 1:
            raise OrderConflictError("A OS foi alterada ou está bloqueada", "stale_order_version")
        await self.session.commit()
        model = await self.session.get(OrderModel, order.order_id)
        await self.session.refresh(model)
        order.version = model.version
        order.create_at = model.create_at
        order.update_at = model.update_at

    async def delete(self, order: Order) -> None:
        logger.debug("Excluindo ordem de serviço no banco: order_id=%s", order.order_id)
        model = await self.session.get(OrderModel, order.order_id)
        if model is None:
            raise OrderNotFoundError()
        await self.session.delete(model)
        await self.session.commit()
        logger.debug("Exclusão de ordem de serviço confirmada: order_id=%s", order.order_id)

    async def get_for_update(self, order_id: int) -> Order | None:
        model = await self.session.scalar(
            select(OrderModel).where(OrderModel.order_id == order_id)
            .with_for_update().execution_options(populate_existing=True)
        )
        return model.to_entity() if model is not None else None

    async def prepare_budget(self, order: Order) -> OrderContext:
        # The same budget row is locked by quotes.update/delete. Its terms cannot
        # change between validation and the commit of request-approval.
        budget = await self.session.scalar(
            select(BudgetModel).where(BudgetModel.budget_id == order.budget_id)
            .with_for_update().execution_options(populate_existing=True)
        )
        vehicle = await self.session.get(VehicleModel, order.vehicle_id)
        technician = await self.session.get(UserModel, order.technical_responser_id)
        snapshot = {name: getattr(budget, name) for name in (
            "budget_id", "client_id", "vehicle_id", "technical_id", "service_name",
            "service_description", "tools", "amount", "duration_service_hours", "duration_service_days",
        )} if budget is not None else None
        return OrderContext(snapshot, vehicle.owner_id if vehicle else None, technician.role if technician else None)

    async def save_action(self, order: Order, event: OrderEvent, expected_version: int) -> Order:
        try:
            values = {name: getattr(order, name) for name in (
                "order_status", "version", "budget_snapshot", "approved_at", "approved_by",
                "execution_started_at", "finished_at", "delivered_at",
            )}
            result = await self.session.execute(
                update(OrderModel).where(OrderModel.order_id == order.order_id,
                                         OrderModel.version == expected_version).values(**values)
            )
            if result.rowcount != 1:
                raise OrderConflictError("A OS foi alterada; consulte a versão atual", "stale_order_version")
            if event.action == "request_approval":
                await self.session.execute(update(BudgetModel).where(
                    BudgetModel.budget_id == order.budget_id,
                ).values(workflow_locked=True))
            self.session.add(OrderEventModel.from_entity(event))
            await self.session.commit()
            return await self.get_by_id(order.order_id)
        except Exception:
            await self.session.rollback()
            raise

    async def history(self, order_id: int, *, offset: int, limit: int) -> list[OrderEvent]:
        models = await self.session.scalars(select(OrderEventModel).where(
            OrderEventModel.order_id == order_id,
        ).order_by(OrderEventModel.version).offset(offset).limit(limit))
        return [model.to_entity() for model in models]
