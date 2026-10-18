from unittest.mock import AsyncMock

import pytest
from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.orm import configure_mappers
from sqlalchemy.schema import CreateTable

from app.modules.quotes.application.dtos.budget_dto import CreateBudgetDTO
from app.modules.quotes.application.use_cases.create_budget import CreateBudgetUseCase
from app.modules.quotes.infrastructure.http.schemas import BudgetReadResponse
from app.modules.quotes.infrastructure.models.budgets_model import BudgetModel
from app.modules.users.infrastructure.models.users_model import UserModel
from app.modules.users.infrastructure.models.vehicles_model import VehicleModel


def test_budget_vehicle_relationship():
    configure_mappers()
    vehicle = VehicleModel(vehicle_id=1)
    technical = UserModel()
    client = UserModel()
    budget = BudgetModel(vehicle=vehicle, technical=technical, client=client)
    assert budget in vehicle.budgets
    assert budget in technical.technical_budgets
    assert budget in client.client_budgets
    column = BudgetModel.__table__.c.vehicle_id
    assert column.references(VehicleModel.__table__.c.vehicle_id)
    assert not column.nullable
    ddl = str(CreateTable(BudgetModel.__table__).compile(dialect=dialect()))
    assert "FOREIGN KEY(vehicle_id) REFERENCES vehicles (vehicle_id)" in ddl


@pytest.mark.asyncio
async def test_create_budget_preserves_vehicle_id():
    dto = CreateBudgetDTO(
        vehicle_id=7, technical_id=1, client_id=2,
        technical_name="Fernando", technical_disponibility=True,
        service_name="Revisão", amount=100,
        duration_service_hours=1, duration_service_days=1,
    )
    repository = AsyncMock()
    budget = await CreateBudgetUseCase(repository).execute(dto)
    repository.save.assert_awaited_once_with(budget)
    assert budget.vehicle_id == 7
    model = BudgetModel.from_entity(budget)
    assert model.vehicle_id == 7
    assert model.to_entity().vehicle_id == 7
    assert BudgetReadResponse.model_validate(model.to_entity()).vehicle_id == 7
