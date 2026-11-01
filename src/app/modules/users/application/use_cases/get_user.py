from app.modules.users.application.exceptions import UserNotFoundError
from app.modules.users.application.ports.user_repository import UserRepository
from app.modules.users.domain.entities.user import User
from app.shared.infrastructure.logging import logger


class GetUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: int) -> User:
        logger.debug("Consultando usuário: user_id=%s", user_id)
        user = await self.user_repository.get_by_id(user_id)
        if user is None:
            logger.debug("Usuário não encontrado: user_id=%s", user_id)
            raise UserNotFoundError()
        logger.debug("Usuário encontrado: user_id=%s", user_id)
        return user

    async def get_by_cpf(self, cpf: str) -> User:
        logger.debug("Consultando usuário por CPF.")
        user = await self.user_repository.get_by_cpf(cpf)
        if user is None:
            logger.debug("Usuário não encontrado por CPF.")
            raise UserNotFoundError()
        logger.debug("Usuário encontrado: user_id=%s", user.id)
        return user
