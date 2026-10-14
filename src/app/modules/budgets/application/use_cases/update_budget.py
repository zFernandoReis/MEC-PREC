from dataclasses import replace

from app.modules.budgets.application.dtos.budget_dto import UpdateBudgetDTO
from app.modules.budgets.application.ports.budget_repository import BudgetRepository
from app.modules.budgets.exceptions import BudgetNotFoundError


class UpdateBudgetUseCase:

    def __init__(
        self,
        budget_repository: BudgetRepository,
    ):
        self.budget_repository = budget_repository

    async def execute(self, budget_id: int, dto: UpdateBudgetDTO):

        budget = await self.budget_repository.get_by_id(budget_id)

        if budget is None:
            raise BudgetNotFoundError()
        
        for field in ("technical_name", "technical_disponibility", "service_name", "service_description", "tools", "amount", "duration_service_hours", "duration_service_days"):
            value = getattr(dto, field)
            if value is not None:
                setattr(budget, field, value)

        await self.budget_repository.update(budget)

        return budget

