from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.modules.quotes.application.dtos.budget_dto import BudgetToolDTO, CreateBudgetDTO
from app.modules.quotes.application.use_cases.create_budget import CreateBudgetUseCase
from app.modules.quotes.domain.entities.stock import Stock
from app.modules.quotes.exceptions import StockNotFoundError
from app.modules.quotes.infrastructure.models.stock_model import StockModel
from app.modules.quotes.infrastructure.repositories.sqlalchemy_stock_repository import (
    SQLAlchemyStockRepository,
)


@pytest.fixture
def payload():
    return {
        "technical_id": 1, "client_id": 2, "vehicle_id": 7,
        "technical_name": "Fernando", "technical_disponibility": True,
        "service_name": "Revisão", "amount": 100,
        "duration_service_hours": 1, "duration_service_days": 1,
        "tools": [{"tool_id": "D703E2-8247", "tool_name": "Chave de catraca", "quantity": 1}],
    }


def stock_item(quantity):
    return Stock(
        tool_id="D703E2-8247", tool_name="Chave de catraca", quantity=quantity,
        price=10, batch="L1", replacement_time_hours=1, replacement_time_days=1,
    )


@pytest.mark.parametrize("quantity", [0, -1])
def test_tool_requires_positive_quantity(payload, quantity):
    with pytest.raises(ValidationError):
        BudgetToolDTO(**{**payload["tools"][0], "quantity": quantity})


@pytest.mark.asyncio
async def test_create_budget_checks_stock_and_serializes_tools(payload):
    budgets, stock = AsyncMock(), AsyncMock()
    stock.get_by_ids.return_value = [stock_item(1)]
    budget = await CreateBudgetUseCase(budgets, stock).execute(CreateBudgetDTO(**payload))
    stock.get_by_ids.assert_awaited_once_with(["D703E2-8247"])
    budgets.save.assert_awaited_once_with(budget)
    assert budget.tools == payload["tools"]
    assert budget.duration_service_hours == 1
    assert budget.duration_service_days == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("quantity", [0, 1])
@pytest.mark.parametrize("technical_available", [True, False])
async def test_insufficient_stock_adds_replacement_once(payload, quantity, technical_available):
    payload["tools"] *= 2
    payload["technical_disponibility"] = technical_available
    budgets, stock = AsyncMock(), AsyncMock()
    stock.get_by_ids.return_value = [stock_item(quantity)]
    budget = await CreateBudgetUseCase(budgets, stock).execute(CreateBudgetDTO(**payload))
    assert budget.duration_service_hours == 2 + (0 if technical_available else 24)
    assert budget.duration_service_days == 2 + (0 if technical_available else 1)
    stock.get_by_ids.assert_awaited_once_with(["D703E2-8247"])
    budgets.save.assert_awaited_once_with(budget)


@pytest.mark.asyncio
async def test_unregistered_tool_prevents_save(payload):
    budgets, stock = AsyncMock(), AsyncMock()
    stock.get_by_ids.return_value = []
    with pytest.raises(StockNotFoundError):
        await CreateBudgetUseCase(budgets, stock).execute(CreateBudgetDTO(**payload))
    budgets.save.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("tools", [None, []])
async def test_budget_without_tools_skips_stock_query(payload, tools):
    payload["tools"] = tools
    budgets, stock = AsyncMock(), AsyncMock()
    budget = await CreateBudgetUseCase(budgets, stock).execute(CreateBudgetDTO(**payload))
    stock.get_by_ids.assert_not_awaited()
    budgets.save.assert_awaited_once_with(budget)
    assert budget.tools == tools


def test_create_budget_http_adds_replacement_for_insufficient_stock(payload, authenticated_app):
    budgets, stock = AsyncMock(), AsyncMock()
    stock.get_by_ids.return_value = [stock_item(0)]
    with TestClient(authenticated_app(budget_repository=budgets, stock_repository=stock)) as client:
        response = client.post("/budgets", json=payload)
    assert response.status_code == 201, response.text
    assert response.json()["duration_service_hours"] == 2
    assert response.json()["duration_service_days"] == 2
    budgets.save.assert_awaited_once()


@pytest.mark.asyncio
async def test_replacement_times_are_summed_only_for_insufficient_tools(payload):
    payload["tools"] += [
        {"tool_id": "SECOND", "tool_name": "Segunda ferramenta", "quantity": 2},
        {"tool_id": "THIRD", "tool_name": "Terceira ferramenta", "quantity": 1},
    ]
    second = stock_item(1)
    second.tool_id = "SECOND"
    second.replacement_time_hours = 2.5
    second.replacement_time_days = 3
    third = stock_item(1)
    third.tool_id = "THIRD"
    budgets, stock = AsyncMock(), AsyncMock()
    stock.get_by_ids.return_value = [stock_item(0), second, third]
    budget = await CreateBudgetUseCase(budgets, stock).execute(CreateBudgetDTO(**payload))
    assert budget.duration_service_hours == 4.5
    assert budget.duration_service_days == 5
    budgets.save.assert_awaited_once_with(budget)


@pytest.mark.asyncio
async def test_stock_repository_filters_ids():
    engine = create_engine("sqlite://")
    StockModel.__table__.create(engine)
    try:
        with Session(engine) as session:
            session.add(StockModel.from_entity(stock_item(3)))
            other = stock_item(10)
            other.tool_id = "OTHER"
            session.add(StockModel.from_entity(other))
            session.commit()
            async_session = AsyncMock(spec=AsyncSession)
            async_session.scalars.side_effect = session.scalars
            repository = SQLAlchemyStockRepository(async_session)
            result = await repository.get_by_ids(["D703E2-8247", "MISSING"])
            assert [(item.tool_id, item.quantity) for item in result] == [("D703E2-8247", 3)]
            assert await repository.get_by_ids([]) == []
            async_session.scalars.assert_awaited_once()
    finally:
        engine.dispose()
