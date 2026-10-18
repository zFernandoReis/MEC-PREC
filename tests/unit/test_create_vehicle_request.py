from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from sqlalchemy import JSON, MetaData, create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.main import create_app
from app.modules.quotes.infrastructure.models.budgets_model import BudgetModel
from app.modules.users.domain.enums.user_role import UserRole
from app.modules.users.infrastructure.models.users_model import UserModel
from app.modules.users.infrastructure.models.vehicles_model import VehicleModel
from app.modules.users.infrastructure.repositories.sqlalchemy_vehicle_repository import (
    SQLAlchemyVehicleRepository,
)


def test_create_vehicle_with_supplied_request():
    payload = {
        "owner_id": 1,
        "vehicle_type": "car",
        "brand": "Fiat",
        "model": "Uno",
        "year_manufacture": 2008,
        "year_model": 2007,
        "license_plate": "MCI6562",
        "color": "black",
        "mileage": 100,
        "fuel_type": "gasoline",
        "chassis": "1234567891234",
        "engine_capacity": 1,
    }
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, record):
        connection.execute("PRAGMA foreign_keys=ON")

    try:
        UserModel.__table__.create(engine)
        VehicleModel.__table__.create(engine)
        # O relacionamento consulta budgets ao excluir um veículo.
        metadata = MetaData()
        UserModel.__table__.to_metadata(metadata)
        VehicleModel.__table__.to_metadata(metadata)
        budgets = BudgetModel.__table__.to_metadata(metadata)
        budgets.c.tools.type = JSON()
        budgets.create(engine)
        with Session(engine) as session:
            session.add(UserModel(
                id=1, primary_name="Fernando", secondary_name="Silva",
                cpf="52998224725", email="fernando@example.com", role=UserRole.CLIENT,
                cep="01001000", street="Praça da Sé", neighborhood="Sé",
                city="São Paulo", state="SP",
            ))
            session.commit()

            # Executa o repositório real em um banco isolado, sem driver async.
            async_session = AsyncMock(spec=AsyncSession)
            async_session.add.side_effect = session.add
            async_session.commit.side_effect = session.commit
            async_session.refresh.side_effect = session.refresh
            async_session.get.side_effect = session.get
            async_session.scalars.side_effect = session.scalars
            async_session.delete.side_effect = session.delete
            repository = SQLAlchemyVehicleRepository(async_session)

            with TestClient(create_app(vehicle_repository=repository)) as client:
                response = client.post("/vehicles", json=payload)
                assert response.status_code == 201, response.text
                body = response.json()
                for field, value in payload.items():
                    assert body[field] == value
                assert body["system_id"]
                assert body["create_at"] and body["update_at"]
                identifier = body["vehicle_id"]
                assert type(identifier) is int
                assert identifier == 1
                assert VehicleModel.__table__.c.vehicle_id.primary_key
                assert VehicleModel.__table__.c.vehicle_id.identity is not None
                assert "id" not in body
                stored = session.get(VehicleModel, identifier)
                assert stored.to_entity().vehicle_id == identifier
                url = f"/vehicles/{identifier}"
                response = client.get(url)
                assert response.status_code == 200, response.text
                assert response.json()["vehicle_id"] == identifier
                response = client.get("/vehicles")
                assert response.status_code == 200, response.text
                assert response.json()[0]["vehicle_id"] == identifier
                response = client.patch(url, json={"color": "white"})
                assert response.status_code == 200, response.text
                assert response.json()["vehicle_id"] == identifier
                assert response.json()["color"] == "white"
                response = client.delete(url)
                assert response.status_code == 204, response.text
                assert session.get(VehicleModel, identifier) is None
                for invalid_id in ("0", "-1", "invalid", "550e8400-e29b-41d4-a716-446655440000"):
                    assert client.get(f"/vehicles/{invalid_id}").status_code == 422
    finally:
        engine.dispose()
