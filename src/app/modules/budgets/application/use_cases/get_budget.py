from app.modules.budgets.application.ports.budget_repository import BudgetRepository
from app.modules.budgets.domain.entities.budget import Budget
from app.modules.users.application.exceptions import UserNotFoundError


class GetBudgetUseCase:
    def __init__(self, budget_repository: BudgetRepository):
        self.budget_repository = budget_repository

    async def execute(self, budget_id: int) -> Budget:
        budget = await self.budget_repository.get_by_id(budget_id)
        if budget is None:
            raise UserNotFoundError()
        return budget
