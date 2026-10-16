from app.modules.quotes.application.dtos.budget_dto import CreateBudgetDTO
from app.modules.quotes.domain.entities.budget import Budget
from app.shared.infrastructure.logging import logger


class CreateBudgetUseCase:

    def __init__(
        self,
          budget_repository,    ):
        self.budget_repository = budget_repository

    async def execute(self, dto: CreateBudgetDTO):
        logger.debug("Iniciando criação de orçamento e cálculo da duração do serviço.")

        if not dto.technical_disponibility:
            logger.debug("Técnico indisponível; acrescentando prazo ao orçamento.")
            duration_hours = dto.duration_service_hours + 24
            duration_days = dto.duration_service_days + 1
            logger.debug("Duração ajustada para %s horas e %s dias.", duration_hours, duration_days)
        else:
            logger.debug("Técnico disponível; mantendo duração informada.")
            duration_hours = dto.duration_service_hours
            duration_days = dto.duration_service_days



        budget = Budget(
            technical_id=dto.technical_id,
            client_id=dto.client_id,
            technical_name=dto.technical_name,
            technical_disponibility=dto.technical_disponibility,
            service_name=dto.service_name,
            service_description=dto.service_description,
            tools=dto.tools,
            amount=dto.amount,
            duration_service_hours=duration_hours,
            duration_service_days=duration_days,
        )

        logger.debug("Persistindo novo orçamento.")
        await self.budget_repository.save(budget)
        logger.debug("Orçamento criado: budget_id=%s", budget.budget_id)

        return budget
