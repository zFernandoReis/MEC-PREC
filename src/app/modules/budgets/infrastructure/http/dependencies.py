from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request

from app.bootstrap.budgets import BudgetsUseCases, build_budgets_use_cases
from app.modules.budgets.application.ports.budget_repository import BudgetRepository
from app.modules.budgets.infrastructure.repositories.sqlalchemy_budget_repository import (
    SQLAlchemyBudgetRepository,
)


async def get_budget_repository(request: Request) -> AsyncGenerator[BudgetRepository, None]:
    repository = request.app.state.budget_repository
    if repository is not None:
        yield repository
        return

    from app.shared.infrastructure.database.engine import AsyncSessionLocal

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
