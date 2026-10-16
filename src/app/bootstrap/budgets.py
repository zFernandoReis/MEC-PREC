from dataclasses import dataclass

from app.modules.quotes.application.ports.budget_repository import BudgetRepository
from app.modules.quotes.application.use_cases.create_budget import CreateBudgetUseCase
from app.modules.quotes.application.use_cases.delete_budget import DeleteBudgetUseCase
from app.modules.quotes.application.use_cases.get_budget import GetBudgetUseCase
from app.modules.quotes.application.use_cases.list_budget import ListBudgetsUseCase
from app.modules.quotes.application.use_cases.update_budget import UpdateBudgetUseCase


@dataclass(frozen=True)
class BudgetsUseCases:
    create_budget: CreateBudgetUseCase
    get_budget: GetBudgetUseCase
    list_budgets: ListBudgetsUseCase
    update_budget: UpdateBudgetUseCase
    delete_budget: DeleteBudgetUseCase


def build_budgets_use_cases(
    budget_repository: BudgetRepository
) -> BudgetsUseCases:
    return BudgetsUseCases(
        create_budget=CreateBudgetUseCase(budget_repository),
        get_budget=GetBudgetUseCase(budget_repository),
        list_budgets=ListBudgetsUseCase(budget_repository),
        update_budget=UpdateBudgetUseCase(budget_repository),
        delete_budget=DeleteBudgetUseCase(budget_repository),
    )
