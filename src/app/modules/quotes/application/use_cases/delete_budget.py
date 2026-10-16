from app.modules.users.application.exceptions import UserNotFoundError
from app.shared.infrastructure.logging import logger


class DeleteBudgetUseCase:

    def __init__(self, budget_repository):
        self.budget_repository = budget_repository

    async def execute(self, budget_id: int) -> None:
        logger.debug("Buscando orçamento para exclusão: budget_id=%s", budget_id)
        budget = await self.budget_repository.get_by_id(budget_id)

        if budget is None:
            logger.debug("Orçamento não encontrado para exclusão: budget_id=%s", budget_id)
            raise UserNotFoundError()

        await self.budget_repository.delete(budget)
        logger.debug("Orçamento excluído: budget_id=%s", budget_id)
