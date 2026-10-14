from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.budgets.domain.entities.budget import Budget
from app.modules.budgets.infrastructure.models.budgets_model import BudgetModel
from app.modules.users.application.exceptions import UserNotFoundError


class SQLAlchemyBudgetRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, budget: Budget) -> None:
        model = BudgetModel.from_entity(budget)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        budget.budget_id = model.budget_id
        budget.create_at = model.create_at
        budget.update_at = model.update_at

    async def get_by_id(self, budget_id: int) -> Budget | None:
        model = await self.session.get(BudgetModel, budget_id)
        return model.to_entity() if model is not None else None

    async def list(self, *, offset: int, limit: int) -> list[Budget]:
        result = await self.session.scalars(
            select(BudgetModel).order_by(BudgetModel.budget_id).offset(offset).limit(limit)
        )
        return [model.to_entity() for model in result]

    async def update(self, budget: Budget) -> None:
        model = await self.session.get(BudgetModel, budget.budget_id)
        if model is None:
            raise UserNotFoundError()
        model.technical_id = budget.technical_id
        model.client_id = budget.client_id
        model.technical_name = budget.technical_name
        model.technical_disponibility = budget.technical_disponibility
        model.service_name = budget.service_name
        model.service_description = budget.service_description
        model.tools = budget.tools
        model.amount = budget.amount
        model.duration_service_hours = budget.duration_service_hours
        model.duration_service_days = budget.duration_service_days
        await self.session.commit()
        await self.session.refresh(model)
        budget.create_at = model.create_at
        budget.update_at = model.update_at

    async def delete(self, budget: Budget) -> None:
        model = await self.session.get(BudgetModel, budget.budget_id)
        if model is None:
            raise UserNotFoundError()
        await self.session.delete(model)
        await self.session.commit()
