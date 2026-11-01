from dataclasses import dataclass

import httpx

from app.modules.users.application.ports.user_repository import UserRepository
from app.modules.users.application.services.address_service import AddressService
from app.modules.users.application.use_cases.create_user import CreateUserUseCase
from app.modules.users.application.use_cases.delete_user import DeleteUserUseCase
from app.modules.users.application.use_cases.get_user import GetUserUseCase
from app.modules.users.application.use_cases.list_users import ListUsersUseCase
from app.modules.users.application.use_cases.update_user import UpdateUserUseCase
from app.modules.users.infrastructure.clients.viacep_client import ViaCepClient
from app.shared.infrastructure.logging import logger


@dataclass(frozen=True)
class UsersUseCases:
    create_user: CreateUserUseCase
    get_user: GetUserUseCase
    list_users: ListUsersUseCase
    update_user: UpdateUserUseCase
    delete_user: DeleteUserUseCase


def build_users_use_cases(
    http_client: httpx.AsyncClient, user_repository: UserRepository
) -> UsersUseCases:
    logger.debug("Montando dependências e casos de uso de usuários.")
    address_service = AddressService(ViaCepClient(http_client))
    return UsersUseCases(
        create_user=CreateUserUseCase(user_repository, address_service),
        get_user=GetUserUseCase(user_repository),
        list_users=ListUsersUseCase(user_repository),
        update_user=UpdateUserUseCase(user_repository, address_service),
        delete_user=DeleteUserUseCase(user_repository),
    )
