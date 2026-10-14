from app.modules.budgets.application.ports.budget_repository import BudgetRepository
from app.modules.budgets.domain.entities.budget import Budget


class ListBudgetsUseCase:
    def __init__(self, budget_repository: BudgetRepository):
        self.budget_repository = budget_repository

    async def execute(self, *, offset: int = 0, limit: int = 100) -> list[Budget]:
        return await self.budget_repository.list(offset=offset, limit=limit)
