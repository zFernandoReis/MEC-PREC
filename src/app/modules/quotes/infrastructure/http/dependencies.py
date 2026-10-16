from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request

from app.bootstrap.budgets import BudgetsUseCases, build_budgets_use_cases
from app.bootstrap.stock import StockUseCases, build_stock_use_cases
from app.modules.quotes.application.ports.budget_repository import BudgetRepository
from app.modules.quotes.application.ports.stock_repository import StockRepository
from app.modules.quotes.infrastructure.repositories.sqlalchemy_budget_repository import (
    SQLAlchemyBudgetRepository,
)
from app.modules.quotes.infrastructure.repositories.sqlalchemy_stock_repository import (
    SQLAlchemyStockRepository,
)
from app.shared.infrastructure.database.engine import AsyncSessionLocal


async def get_budget_repository(request: Request) -> AsyncGenerator[BudgetRepository, None]:
    repository = request.app.state.budget_repository
    if repository is not None:
        yield repository
        return

    

    async with AsyncSessionLocal() as session:
        try:
            yield SQLAlchemyBudgetRepository(session)
        except Exception:
            await session.rollback()
            raise


def get_budgets_use_cases(
    request: Request,
    repository: Annotated[BudgetRepository, Depends(get_budget_repository)],
) -> BudgetsUseCases:
    return build_budgets_use_cases(repository)


async def get_stock_repository(request: Request) -> AsyncGenerator[StockRepository, None]:
    repository = request.app.state.stock_repository
    if repository is not None:
        yield repository
        return

    
    async with AsyncSessionLocal() as session:
        try:
            yield SQLAlchemyStockRepository(session)
        except Exception:
            await session.rollback()
            raise

def get_stock_use_cases(
    request: Request,
    repository: Annotated[StockRepository, Depends(get_stock_repository)],
) -> StockUseCases:
    return build_stock_use_cases(repository)
