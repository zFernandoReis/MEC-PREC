from app.modules.users.application.exceptions import UserNotFoundError


class DeleteBudgetUseCase:

    def __init__(self, budget_repository):
        self.budget_repository = budget_repository

    async def execute(self, budget_id: int) -> None:
        budget = await self.budget_repository.get_by_id(budget_id)

        if budget is None:
            raise UserNotFoundError()

        await self.budget_repository.delete(budget)
