from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request

from app.bootstrap.users import UsersUseCases, build_users_use_cases
from app.modules.users.application.ports.user_repository import UserRepository
from app.modules.users.infrastructure.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)


async def get_user_repository(request: Request) -> AsyncGenerator[UserRepository, None]:
    repository = request.app.state.user_repository
    if repository is not None:
        yield repository
        return

    from app.shared.infrastructure.database.engine import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        try:
            yield SQLAlchemyUserRepository(session)
        except Exception:
            await session.rollback()
            raise


def get_users_use_cases(
    request: Request,
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> UsersUseCases:
    return build_users_use_cases(request.app.state.http_client, repository)
