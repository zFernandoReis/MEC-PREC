from dataclasses import replace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.modules.users.domain.entities.user import User
from app.modules.users.domain.enums.user_role import UserRole
from app.modules.users.domain.value_objects.address import Address
from app.modules.users.infrastructure.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)
from app.shared.infrastructure.database.base import Base


@pytest.mark.asyncio
async def test_repository_crud_and_duplicate_cpf():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    user = User(
        id=None, primary_name="Fernando", secondary_name="Reis",
        cpf="52998224725", email="fernando@example.com", role=UserRole.ADMIN,
        adress=Address(
            cep="01001000", street="Praça da Sé", neighborhood="Sé",
            city="São Paulo", state="SP", number="196", complement="Sala 1",
        ),
    )
    try:
        with Session(engine) as sync_session:
            # Adaptador de teste: executa operações reais em SQLite sem driver async.
            session = AsyncMock(spec=AsyncSession)
            session.add.side_effect = sync_session.add
            session.commit.side_effect = sync_session.commit
            session.get.side_effect = sync_session.get
            session.scalars.side_effect = sync_session.scalars
            session.scalar.side_effect = sync_session.scalar
            session.delete.side_effect = sync_session.delete
            session.refresh.side_effect = sync_session.refresh
            repository = SQLAlchemyUserRepository(session)

            await repository.save(user)
            assert user.id == 1
            assert user.create_at is not None
            assert user.update_at is not None
            assert await repository.get_by_id(user.id) == user
            assert await repository.get_by_cpf(user.cpf) == user
            assert await repository.get_by_cpf("12345678909") is None
            assert await repository.list(offset=0, limit=10) == [user]
            assert await repository.list(offset=1, limit=10) == []

            sync_session.execute(text(
                "UPDATE users SET update_at = '2000-01-01 00:00:00'"
            ))
            sync_session.commit()
            sync_session.expire_all()

            user.primary_name = "Roberto"
            user.change_address(replace(user.adress, number="20", complement=None))
            await repository.update(user)
            assert user.update_at.year > 2000
            assert await repository.get_by_id(user.id) == user

            with pytest.raises(IntegrityError):
                await repository.save(replace(user, id=None, system_id=uuid4()))
            sync_session.rollback()
            assert await repository.get_by_id(user.id) == user

            second_user = replace(
                user, id=None, system_id=uuid4(), cpf="11144477735",
                create_at=None, update_at=None,
            )
            await repository.save(second_user)
            assert second_user.id == 2
            assert second_user.system_id != user.system_id

            await repository.delete(user)
            assert await repository.get_by_id(user.id) is None
            assert await repository.list(offset=0, limit=10) == [second_user]
    finally:
        engine.dispose()
