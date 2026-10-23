from collections import Counter

from app.modules.quotes.application.dtos.budget_dto import CreateBudgetDTO
from app.modules.quotes.application.ports.budget_repository import BudgetRepository
from app.modules.quotes.application.ports.stock_repository import StockRepository
from app.modules.quotes.domain.entities.budget import Budget
from app.modules.quotes.exceptions import StockNotFoundError
from app.shared.infrastructure.logging import logger


class CreateBudgetUseCase:

    def __init__(
        self,
        budget_repository: BudgetRepository,
        stock_repository: StockRepository,
    ):
        self.budget_repository = budget_repository
        self.stock_repository = stock_repository

    async def execute(self, dto: CreateBudgetDTO):
        logger.debug("Iniciando criação de orçamento e cálculo da duração do serviço.")

        required = Counter()
        for tool in dto.tools or []:
            required[tool.tool_id] += tool.quantity

        replacement_hours = 0
        replacement_days = 0
        if required:
            stock_items = await self.stock_repository.get_by_ids(list(required))
            available = {item.tool_id: item for item in stock_items}
            for tool_id, quantity in required.items():
                item = available.get(tool_id)
                if item is None:
                    raise StockNotFoundError()
                if item.quantity < quantity:
                    replacement_hours += item.replacement_time_hours or 0
                    replacement_days += item.replacement_time_days or 0
                    logger.debug("Acrescentando prazo de reposição: tool_id=%s", tool_id)

        if not dto.technical_disponibility:
            logger.debug("Técnico indisponível; acrescentando prazo ao orçamento.")
            duration_hours = dto.duration_service_hours + 24
            duration_days = dto.duration_service_days + 1
            logger.debug("Duração ajustada para %s horas e %s dias.", duration_hours, duration_days)
        else:
            logger.debug("Técnico disponível; mantendo duração informada.")
            duration_hours = dto.duration_service_hours
            duration_days = dto.duration_service_days
        duration_hours += replacement_hours
        duration_days += replacement_days

        budget = Budget(
            technical_id=dto.technical_id,
            client_id=dto.client_id,
            vehicle_id=dto.vehicle_id,
            technical_name=dto.technical_name,
            technical_disponibility=dto.technical_disponibility,
            service_name=dto.service_name,
            service_description=dto.service_description,
            tools=[tool.model_dump() for tool in dto.tools] if dto.tools is not None else None,
            amount=dto.amount,
            duration_service_hours=duration_hours,
            duration_service_days=duration_days,
        )

        logger.debug("Persistindo novo orçamento.")
        await self.budget_repository.save(budget)
        logger.debug("Orçamento criado: budget_id=%s", budget.budget_id)

        return budget
