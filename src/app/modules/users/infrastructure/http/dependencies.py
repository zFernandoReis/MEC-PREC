from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request

from app.bootstrap.users import UsersUseCases, build_users_use_cases
from app.bootstrap.vehicles import VehiclesUseCases, build_vehicles_use_cases
from app.modules.users.application.ports.user_repository import UserRepository
from app.modules.users.application.ports.vehicle_repository import VehicleRepository
from app.modules.users.infrastructure.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)
from app.modules.users.infrastructure.repositories.sqlalchemy_vehicle_repository import (
    SQLAlchemyVehicleRepository,
)
from app.shared.infrastructure.database.engine import AsyncSessionLocal
from app.shared.infrastructure.logging import logger


async def get_user_repository(request: Request) -> AsyncGenerator[UserRepository, None]:
    repository = request.app.state.user_repository
    if repository is not None:
        logger.debug("Usando repositório fornecido na configuração da aplicação.")
        yield repository
        return

    logger.debug("Abrindo sessão de banco para a requisição.")
    async with AsyncSessionLocal() as session:
        try:
            yield SQLAlchemyUserRepository(session)
        except Exception:
            logger.debug("Revertendo transação após falha no processamento da requisição.")
            await session.rollback()
            raise


def get_users_use_cases(
    request: Request,
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> UsersUseCases:
    return build_users_use_cases(request.app.state.http_client, repository)


async def get_vehicles_repository(request: Request) -> AsyncGenerator[VehicleRepository, None]:
    repository = request.app.state.vehicle_repository
    if repository is not None:
        logger.debug("Usando repositório fornecido na configuração da aplicação.")
        yield repository
        return

    logger.debug("Abrindo sessão de banco para a requisição.")
    async with AsyncSessionLocal() as session:
        try:
            yield SQLAlchemyVehicleRepository(session)
        except Exception:
            logger.debug("Revertendo transação após falha no processamento da requisição.")
            await session.rollback()
            raise


def get_vehicles_use_cases(
    repository: Annotated[VehicleRepository, Depends(get_vehicles_repository)],
) -> VehiclesUseCases:
    return build_vehicles_use_cases(repository)
    