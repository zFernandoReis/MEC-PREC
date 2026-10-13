import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.modules.users.domain.entities.user import User
from app.modules.users.domain.enums.user_role import UserRole
from app.modules.users.domain.value_objects.address import Address
from app.modules.users.infrastructure.models.client_model import ClientModel
from app.shared.infrastructure.database.base import Base


@pytest.mark.parametrize("role", list(UserRole))
def test_persist_and_restore_entity(role):
    user = User(
        id=None, primary_name="Fernando", secondary_name="Silva",
        cpf="52998224725", email="fernando@example.com", role=role,
        adress=Address(
            cep="01001000", street="Praça da Sé", neighborhood="Sé",
            city="São Paulo", state="SP", number="10", complement=None,
        ),
    )
    engine = create_engine("sqlite://")
    try:
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            session.add(ClientModel.from_entity(user))
            session.commit()

        with Session(engine) as session:
            model = session.scalars(select(ClientModel)).one()
            restored = model.to_entity()
            assert restored.id == 1
            assert restored.system_id == user.system_id
            assert restored.create_at is not None
            assert restored.update_at is not None
            assert restored.primary_name == user.primary_name
            assert restored.role == user.role
            assert model.address == user.adress
            assert session.connection().exec_driver_sql(
                "SELECT role FROM cliente"
            ).scalar_one() == role.value
            model.address = Address(
                cep="20040002", street="Rua da Assembleia", neighborhood="Centro",
                city="Rio de Janeiro", state="RJ", number=None, complement="Sala 2",
            )
            session.commit()
            assert model.to_entity().adress.city == "Rio de Janeiro"
            assert model.number is None
            assert model.complement == "Sala 2"
    finally:
        engine.dispose()
