from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.bootstrap.budgets import BudgetsUseCases
from app.modules.budgets.application.dtos.budget_dto import (
    CreateBudgetDTO,
    UpdateBudgetDTO,
)
from app.modules.budgets.infrastructure.http.dependencies import (
    get_budgets_use_cases,
)
from app.modules.budgets.infrastructure.http.schemas import (
    BudgetReadResponse,
    BudgetResponse,
)

router = APIRouter(prefix="/budgets", tags=["Budgets"])
UseCases = Annotated[BudgetsUseCases, Depends(get_budgets_use_cases)]
BudgetId = Annotated[int, Path(ge=1)]


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
async def create_budget(dto: CreateBudgetDTO, use_cases: UseCases):
    return await use_cases.create_budget.execute(dto)


@router.get("", response_model=list[BudgetReadResponse])
async def list_budgets(
    use_cases: UseCases,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
):
    return await use_cases.list_budgets.execute(offset=offset, limit=limit)


@router.get("/{budget_id}", response_model=BudgetReadResponse)
async def get_budget(budget_id: BudgetId, use_cases: UseCases):
    return await use_cases.get_budget.execute(budget_id)


@router.patch("/{budget_id}", response_model=BudgetResponse)
async def update_budget(budget_id: BudgetId, dto: UpdateBudgetDTO, use_cases: UseCases):
    return await use_cases.update_budget.execute(budget_id, dto)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(budget_id: BudgetId, use_cases: UseCases):
    await use_cases.delete_budget.execute(budget_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
