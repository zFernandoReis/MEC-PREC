from dataclasses import dataclass

from app.modules.quotes.application.ports.budget_repository import BudgetRepository
from app.modules.quotes.application.ports.stock_repository import StockRepository
from app.modules.quotes.application.use_cases.create_budget import CreateBudgetUseCase
from app.modules.quotes.application.use_cases.delete_budget import DeleteBudgetUseCase
from app.modules.quotes.application.use_cases.get_budget import GetBudgetUseCase
from app.modules.quotes.application.use_cases.get_stock import GetStockUseCase
from app.modules.quotes.application.use_cases.list_budget import ListBudgetsUseCase
from app.modules.quotes.application.use_cases.update_budget import UpdateBudgetUseCase
from app.shared.infrastructure.logging import logger


@dataclass(frozen=True)
class BudgetsUseCases:
    create_budget: CreateBudgetUseCase
    get_budget: GetBudgetUseCase
    get_stock: GetStockUseCase
    list_budgets: ListBudgetsUseCase
    update_budget: UpdateBudgetUseCase
    delete_budget: DeleteBudgetUseCase


def build_budgets_use_cases(
    budget_repository: BudgetRepository,
    stock_repository: StockRepository,
) -> BudgetsUseCases:
    logger.debug("Montando dependências e casos de uso de orçamentos.")
    return BudgetsUseCases(
        create_budget=CreateBudgetUseCase(budget_repository, stock_repository),
        get_budget=GetBudgetUseCase(budget_repository),
        get_stock=GetStockUseCase(budget_repository),
        list_budgets=ListBudgetsUseCase(budget_repository),
        update_budget=UpdateBudgetUseCase(budget_repository),
        delete_budget=DeleteBudgetUseCase(budget_repository),
    )
