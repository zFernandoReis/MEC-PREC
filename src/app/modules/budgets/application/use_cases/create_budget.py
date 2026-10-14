from app.modules.budgets.application.dtos.budget_dto import CreateBudgetDTO
from app.modules.budgets.domain.entities.budget import Budget


class CreateBudgetUseCase:

    def __init__(
        self,
          budget_repository,    ):
        self.budget_repository = budget_repository

    async def execute(self, dto: CreateBudgetDTO):

        if not dto.technical_disponibility:
            print("technical is not available for this budget.")
            duration_hours = dto.duration_service_hours + 24
            duration_days = dto.duration_service_days + 1
            print(f"Duration adjusted to {duration_hours} hours and {duration_days} days.")
        else:
            duration_hours = dto.duration_service_hours
            duration_days = dto.duration_service_days



        budget = Budget(
            budget_id=dto.budget_id,
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

        await self.budget_repository.save(budget)

        return budget
