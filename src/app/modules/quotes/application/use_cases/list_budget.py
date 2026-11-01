from app.modules.quotes.application.ports.budget_repository import BudgetRepository
from app.modules.quotes.domain.entities.budget import Budget
from app.shared.infrastructure.logging import logger


class ListBudgetsUseCase:
    def __init__(self, budget_repository: BudgetRepository):
        self.budget_repository = budget_repository

    async def execute(self, *, offset: int = 0, limit: int = 100) -> list[Budget]:
        logger.debug("Listando orçamentos: offset=%s, limit=%s", offset, limit)
        budgets = await self.budget_repository.list(offset=offset, limit=limit)
        logger.debug("Listagem de orçamentos concluída: quantidade=%s", len(budgets))
        return budgets
