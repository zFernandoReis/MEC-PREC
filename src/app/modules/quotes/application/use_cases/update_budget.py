from dataclasses import replace

from app.modules.quotes.application.dtos.budget_dto import UpdateBudgetDTO
from app.modules.quotes.application.ports.budget_repository import BudgetRepository
from app.modules.quotes.exceptions import BudgetNotFoundError
from app.shared.infrastructure.logging import logger


class UpdateBudgetUseCase:

    def __init__(
        self,
        budget_repository: BudgetRepository,
    ):
        self.budget_repository = budget_repository

    async def execute(self, budget_id: int, dto: UpdateBudgetDTO):
        logger.debug("Buscando orçamento para atualização: budget_id=%s", budget_id)

        budget = await self.budget_repository.get_by_id(budget_id)

        if budget is None:
            logger.debug("Orçamento não encontrado para atualização: budget_id=%s", budget_id)
            raise BudgetNotFoundError()
        
        for field in ("technical_name", "technical_disponibility", "service_name", "service_description", "tools", "amount", "duration_service_hours", "duration_service_days"):
            value = getattr(dto, field)
            if value is not None:
                setattr(budget, field, value)

        logger.debug("Persistindo alterações do orçamento: budget_id=%s", budget_id)
        await self.budget_repository.update(budget)
        logger.debug("Orçamento atualizado: budget_id=%s", budget_id)

        return budget

